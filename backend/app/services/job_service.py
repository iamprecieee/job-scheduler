import time
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency import JobDependency
from app.models.job import Job, JobStatus
from app.scheduler.dag import detect_cycle
from app.scheduler.worker import job_queue
from app.schemas.job import CreateJobRequest, JobListResponse, JobResponse


class JobService:
    @staticmethod
    async def create_job(session: AsyncSession, request: CreateJobRequest) -> JobResponse:
        now = datetime.now(UTC)

        job = Job(
            type=request.type,
            payload=request.payload,
            priority=request.priority,
            effective_priority=float(request.priority),
            scheduled_at=request.scheduled_at,
            recurring_interval=request.recurring_interval,
            status=JobStatus.PENDING,
            retry_count=0,
            created_at=now,
        )
        session.add(job)
        await session.flush()

        if request.dependencies:
            edges_stmt = select(JobDependency.job_id, JobDependency.depends_on_job_id)
            edges_result = await session.execute(edges_stmt)
            existing_edges = [(row.job_id, row.depends_on_job_id) for row in edges_result.all()]

            if detect_cycle(job.id, request.dependencies, existing_edges):
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="Adding these dependencies would create a cycle."
                )

            dep_check_stmt = select(func.count()).where(Job.id.in_(request.dependencies))
            dep_count_result = await session.execute(dep_check_stmt)
            if dep_count_result.scalar() != len(request.dependencies):
                await session.rollback()
                raise HTTPException(
                    status_code=400, detail="One or more dependencies do not exist."
                )

            for dep_id in request.dependencies:
                dep_record = JobDependency(job_id=job.id, depends_on_job_id=dep_id)
                session.add(dep_record)

        await session.commit()
        await session.refresh(job)

        scheduled_timestamp = job.scheduled_at.timestamp() if job.scheduled_at else time.time()
        job_queue.push(
            str(job.id), job.effective_priority, scheduled_timestamp, job.created_at.timestamp()
        )

        logger.info(
            "Job {} created | type={} priority={} scheduled={}",
            job.id,
            job.type,
            job.priority,
            bool(job.scheduled_at),
        )

        return JobResponse.model_validate(job)

    @staticmethod
    async def get_job(session: AsyncSession, job_id: uuid.UUID) -> JobResponse:
        job = await session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse.model_validate(job)

    @staticmethod
    async def list_jobs(
        session: AsyncSession, skip: int = 0, limit: int = 100, status: str | None = None
    ) -> JobListResponse:
        stmt = select(Job).order_by(desc(Job.created_at)).offset(skip).limit(limit)
        count_stmt = select(func.count()).select_from(Job)

        if status:
            stmt = stmt.where(Job.status == status)
            count_stmt = count_stmt.where(Job.status == status)

        result = await session.execute(stmt)
        jobs = result.scalars().all()

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        return JobListResponse(jobs=[JobResponse.model_validate(j) for j in jobs], total=total)

    @staticmethod
    async def cancel_job(session: AsyncSession, job_id: uuid.UUID) -> JobResponse:
        """Cancel a pending or processing job.

        If a job is already PROCESSING, cancelling it sets the status to CANCELLED
        and removes it from the queue, but it does NOT interrupt the currently running
        handler execution. The handler will run to completion.
        """
        job = await session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job in status {job.status}")

        job.status = JobStatus.CANCELLED
        await session.commit()
        await session.refresh(job)

        job_queue.remove(str(job.id))

        logger.info("Job {} cancelled", job.id)

        return JobResponse.model_validate(job)
