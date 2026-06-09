import time
import uuid
from datetime import UTC

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dlq import DeadLetterEntry
from app.models.job import JobStatus
from app.scheduler.worker import job_queue
from app.schemas.dlq import DLQEntryResponse, DLQListResponse


class DLQService:
    @staticmethod
    async def list_dlq(session: AsyncSession, skip: int = 0, limit: int = 100) -> DLQListResponse:
        stmt = (
            select(DeadLetterEntry)
            .options(selectinload(DeadLetterEntry.job))
            .order_by(desc(DeadLetterEntry.entered_at))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        entries = result.scalars().all()

        count_stmt = select(func.count()).select_from(DeadLetterEntry)
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        return DLQListResponse(
            entries=[DLQEntryResponse.model_validate(e) for e in entries], total=total
        )

    @staticmethod
    async def replay_job(session: AsyncSession, entry_id: uuid.UUID) -> DLQEntryResponse:
        stmt = (
            select(DeadLetterEntry)
            .options(selectinload(DeadLetterEntry.job))
            .where(DeadLetterEntry.id == entry_id)
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(status_code=404, detail="DLQ entry not found")

        job = entry.job
        if not job:
            raise HTTPException(status_code=404, detail="Associated job not found")

        job.status = JobStatus.PENDING
        job.retry_count = 0
        job.error_message = None

        from datetime import datetime

        now = datetime.now(UTC)
        entry.retry_attempted_at = now

        await session.commit()
        await session.refresh(entry)

        job_queue.push(str(job.id), job.effective_priority, time.time(), job.created_at.timestamp())

        return DLQEntryResponse.model_validate(entry)
