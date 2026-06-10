import asyncio
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def broadcast_new_email(email: SentEmailResponse) -> None:
    payload = json.dumps(
        {
            "id": str(email.id),
            "job_id": str(email.job_id),
            "recipient": email.recipient,
            "subject": email.subject,
            "body": email.body,
            "sent_at": email.sent_at.isoformat(),
        }
    )
    for queue in list(_inbox_subscribers):
        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            pass


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
        await broadcast_new_email(response)

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
