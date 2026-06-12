import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import asyncpg
from loguru import logger
from sqlalchemy import desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import SentEmail
from app.schemas import SentEmailListResponse, SentEmailResponse

_inbox_subscribers: list[asyncio.Queue[str]] = []


def subscribe_inbox() -> asyncio.Queue[str]:
    """Register a new SSE subscriber for inbox events."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    _inbox_subscribers.append(queue)
    return queue


def unsubscribe_inbox(queue: asyncio.Queue[str]) -> None:
    """Remove an SSE subscriber."""
    try:
        _inbox_subscribers.remove(queue)
    except ValueError:
        pass


def _broadcast_new_email_local(payload: str) -> None:
    for queue in list(_inbox_subscribers):
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass


async def pubsub_listener_loop() -> None:
    """Continuously listens for Postgres 'new_email' notifications."""
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    async def handle_notification(
        connection: asyncpg.Connection, pid: int, channel: str, payload: str
    ) -> None:
        _broadcast_new_email_local(payload)

    while True:
        conn: asyncpg.Connection | None = None
        try:
            conn = await asyncpg.connect(db_url)
            assert conn is not None
            await conn.add_listener("new_email", handle_notification)
            logger.info("Connected to Postgres Pub/Sub channel 'new_email'")

            while not conn.is_closed():
                await asyncio.sleep(5.0)

        except asyncio.CancelledError:
            if conn is not None and not conn.is_closed():
                await conn.remove_listener("new_email", handle_notification)
                await conn.close()
            logger.info("PubSub listener loop cancelled")
            break
        except Exception as exc:
            logger.error("PubSub listener error: {}", exc)
            await asyncio.sleep(5.0)


class EmailService:
    @staticmethod
    async def record_email(
        session: AsyncSession,
        job_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> SentEmail:
        """Persist a successfully sent email and broadcast to SSE listeners."""
        email = SentEmail(
            job_id=job_id,
            recipient=payload["to"],
            subject=payload["subject"],
            body=payload["body"],
            sent_at=datetime.now(UTC),
        )
        session.add(email)
        await session.flush()

        response = SentEmailResponse.model_validate(email)
        payload = json.dumps(
            {
                "id": str(response.id),
                "job_id": str(response.job_id),
                "recipient": response.recipient,
                "subject": response.subject,
                "body": response.body,
                "sent_at": response.sent_at.isoformat(),
            }
        )
        await session.execute(text("SELECT pg_notify('new_email', :payload)"), {"payload": payload})

        logger.info("Recorded sent email for job {} → {}", job_id, payload["to"])
        return email

    @staticmethod
    async def list_emails(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 50,
    ) -> SentEmailListResponse:
        """Return a paginated list of sent emails, newest first."""
        stmt = select(SentEmail).order_by(desc(SentEmail.sent_at)).offset(skip).limit(limit)
        result = await session.execute(stmt)
        emails = result.scalars().all()

        count_stmt = select(func.count()).select_from(SentEmail)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        return SentEmailListResponse(
            emails=[SentEmailResponse.model_validate(e) for e in emails],
            total=total,
        )
