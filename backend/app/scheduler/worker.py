import asyncio
import random
import time
import uuid
from datetime import UTC, datetime, timedelta

from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.handlers import get_handler
from app.models.dependency import JobDependency
from app.models.dlq import DeadLetterEntry
from app.models.job import Job, JobStatus
from app.scheduler.base import SchedulerQueue
from app.scheduler.heap_queue import HeapQueue

job_queue: SchedulerQueue = HeapQueue()


def get_retry_jitter(attempt: int) -> float:
    if attempt == 1:
        return 1.0 + random.uniform(-0.5, 0.5)
    elif attempt == 2:
        return 5.0 + random.uniform(-2.0, 2.0)
    else:
        return 25.0 + random.uniform(-5.0, 5.0)


async def process_job(job_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        stmt = (
            select(Job)
            .where(Job.id == job_id)
            .where(Job.status.in_([JobStatus.PENDING, JobStatus.PROCESSING]))
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()

        if not job or job.status == JobStatus.CANCELLED:
            return

        dep_stmt = (
            select(Job)
            .join(JobDependency, JobDependency.depends_on_job_id == Job.id)
            .where(JobDependency.job_id == job.id)
        )
        dep_result = await session.execute(dep_stmt)
        dependencies = dep_result.scalars().all()

        if any(d.status != JobStatus.COMPLETED for d in dependencies):
            # Dependency not yet satisfied — re-enqueue with a short backoff.
            delay = 5.0
            scheduled = time.time() + delay
            job_queue.push(
                str(job.id), job.effective_priority, scheduled, job.created_at.timestamp()
            )
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(UTC)
        await session.commit()

        try:
            handler = get_handler(job.type)
            await handler.execute(job.payload)

            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(UTC)

            if job.recurring_interval:
                base_time = job.scheduled_at or datetime.now(UTC)
                next_run = None
                if job.recurring_interval == "every_1_minute":
                    next_run = base_time + timedelta(minutes=1)
                elif job.recurring_interval == "every_5_minutes":
                    next_run = base_time + timedelta(minutes=5)
                elif job.recurring_interval == "every_1_hour":
                    next_run = base_time + timedelta(hours=1)

                if next_run:
                    new_job = Job(
                        type=job.type,
                        payload=job.payload,
                        priority=job.priority,
                        effective_priority=float(job.priority),
                        scheduled_at=next_run,
                        recurring_interval=job.recurring_interval,
                    )
                    session.add(new_job)
                    await session.flush()
                    job_queue.push(
                        str(new_job.id),
                        new_job.effective_priority,
                        next_run.timestamp(),
                        new_job.created_at.timestamp(),
                    )

            await session.commit()
            logger.info("Job {} completed", job.id)

        except Exception as exc:
            # Log with full traceback so post-mortems have context.
            logger.opt(exception=True).error("Job {} failed: {}", job.id, exc)

            job.retry_count += 1
            job.error_message = str(exc)

            if job.retry_count > settings.max_retries:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now(UTC)

                dlq_entry = DeadLetterEntry(job_id=job.id, failure_reason=str(exc))
                session.add(dlq_entry)
                logger.warning(
                    "Job {} exhausted {} retries — moved to DLQ",
                    job.id,
                    settings.max_retries,
                )
            else:
                job.status = JobStatus.PENDING
                job.started_at = None

                jitter = get_retry_jitter(job.retry_count)
                next_run_ts = time.time() + jitter
                job.scheduled_at = datetime.fromtimestamp(next_run_ts, tz=UTC)

                logger.info(
                    "Job {} retry {} scheduled in {:.2f}s",
                    job.id,
                    job.retry_count,
                    jitter,
                )
                job_queue.push(
                    str(job.id), job.effective_priority, next_run_ts, job.created_at.timestamp()
                )

            await session.commit()


async def worker_loop() -> None:
    logger.info("Worker loop started")

    while True:
        try:
            job_id_str = job_queue.pop()

            if job_id_str:
                job_id = uuid.UUID(job_id_str)
                asyncio.create_task(process_job(job_id))
            else:
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("Worker loop cancelled")
            break
        except Exception as exc:
            logger.opt(exception=True).error("Worker loop error: {}", exc)
            await asyncio.sleep(1.0)


async def db_sync_loop() -> None:
    logger.info("DB sync loop started")

    while True:
        try:
            async with async_session_factory() as session:
                stmt = (
                    select(Job)
                    .where(Job.status == JobStatus.PENDING)
                    .order_by(Job.scheduled_at.nulls_first(), Job.effective_priority)
                    .limit(100)
                )
                result = await session.execute(stmt)
                jobs = result.scalars().all()

                for job in jobs:
                    scheduled = job.scheduled_at.timestamp() if job.scheduled_at else time.time()
                    job_queue.push(
                        str(job.id), job.effective_priority, scheduled, job.created_at.timestamp()
                    )

            await asyncio.sleep(settings.worker_poll_interval_seconds)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.opt(exception=True).error("DB sync loop error: {}", exc)
            await asyncio.sleep(5.0)


async def aging_loop() -> None:
    from app.scheduler.aging import recalculate_effective_priority

    logger.info("Aging loop started")

    while True:
        try:
            await asyncio.sleep(settings.aging_recalc_interval_seconds)

            async with async_session_factory() as session:
                now = datetime.now(UTC)

                stmt = select(Job).where(Job.status == JobStatus.PENDING)
                result = await session.execute(stmt)
                jobs = result.scalars().all()

                updated_count = 0
                for job in jobs:
                    base_time = job.started_at or job.created_at
                    age_seconds = (now - base_time).total_seconds()

                    new_priority = recalculate_effective_priority(
                        base_priority=job.priority,
                        age_seconds=age_seconds,
                        threshold_seconds=settings.aging_threshold_seconds,
                        weight=settings.aging_weight,
                    )

                    if abs(new_priority - job.effective_priority) > 0.01:
                        job.effective_priority = new_priority
                        updated_count += 1

                        scheduled = (
                            job.scheduled_at.timestamp() if job.scheduled_at else time.time()
                        )
                        job_queue.push(
                            str(job.id), new_priority, scheduled, job.created_at.timestamp()
                        )

                if updated_count > 0:
                    await session.commit()
                    logger.debug("Aged {} jobs", updated_count)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.opt(exception=True).error("Aging loop error: {}", exc)
            await asyncio.sleep(5.0)
