from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import func, select, text

from app.config import settings
from app.models.dlq import DeadLetterEntry
from app.models.job import Job, JobStatus


async def check_and_trigger_alert(session) -> None:
    """Instantly checks DLQ threshold and triggers an alert job if needed.
    Uses Postgres advisory locks to prevent duplicate alerts from concurrent workers.
    """

    await session.execute(text("SELECT pg_advisory_xact_lock(1001)"))

    count_stmt = select(func.count()).select_from(DeadLetterEntry)
    result = await session.execute(count_stmt)
    dlq_count = result.scalar() or 0

    if dlq_count >= settings.dlq_alert_threshold:
        alert_cooldown_seconds = 3600
        now = datetime.now(UTC)

        last_alert_stmt = (
            select(Job.created_at)
            .where(Job.type == "send_email")
            .where(
                Job.payload.op("->>")("subject").like(
                    "ALERT: Job Scheduler DLQ Threshold Exceeded%"
                )
            )
            .order_by(Job.created_at.desc())
            .limit(1)
        )
        last_alert_res = await session.execute(last_alert_stmt)
        last_alert_time = last_alert_res.scalar()

        if (
            last_alert_time is None
            or (now - last_alert_time).total_seconds() > alert_cooldown_seconds
        ):
            logger.warning(f"DLQ threshold exceeded instantly! Count: {dlq_count}")

            email_payload = {
                "to": settings.alert_email_to,
                "subject": f"ALERT: Job Scheduler DLQ Threshold Exceeded ({dlq_count} jobs)",
                "body": f"Dead Letter Queue has {dlq_count} failed jobs.",
            }

            alert_job = Job(
                type="send_email",
                payload=email_payload,
                priority=1,
                effective_priority=1.0,
                status=JobStatus.PENDING,
                scheduled_at=now,
            )
            session.add(alert_job)
