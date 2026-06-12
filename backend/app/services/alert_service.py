import asyncio
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import func, select

from app.config import settings
from app.database import async_session_factory
from app.models.dlq import DeadLetterEntry
from app.models.job import Job, JobStatus


async def alert_loop() -> None:
    """Background task that monitors the DLQ and sends alerts if threshold is exceeded."""
    logger.info("Alert loop started")

    last_alert_time: datetime | None = None
    alert_cooldown_seconds = 3600  # Only alert once an hour at most

    while True:
        try:
            await asyncio.sleep(60)  # Check every minute

            async with async_session_factory() as session:
                count_stmt = select(func.count()).select_from(DeadLetterEntry)
                result = await session.execute(count_stmt)
                dlq_count = result.scalar() or 0

                if dlq_count >= settings.dlq_alert_threshold:
                    now = datetime.now(UTC)
                    if (
                        last_alert_time is None
                        or (now - last_alert_time).total_seconds() > alert_cooldown_seconds
                    ):
                        logger.warning(f"DLQ threshold exceeded! Count: {dlq_count}")

                        email_payload = {
                            "to": settings.alert_email_to,
                            "subject": (
                                f"ALERT: Job Scheduler DLQ Threshold Exceeded ({dlq_count} jobs)"
                            ),
                            "body": f"Dead Letter Queue has {dlq_count} failed jobs.",
                        }

                        alert_job = Job(
                            type="send_email",
                            payload=email_payload,
                            priority=1,  # High priority
                            status=JobStatus.PENDING,
                            scheduled_at=now
                        )
                        session.add(alert_job)
                        await session.commit()

                        last_alert_time = now

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Alert loop error: {e}")
            await asyncio.sleep(5.0)
