import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.dlq import DLQEntryResponse, DLQListResponse
from app.services.dlq_service import DLQService

router = APIRouter(prefix="/dlq", tags=["DLQ"])


@router.get("", response_model=DLQListResponse)
async def list_dlq(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> DLQListResponse:
    """List all dead letter queue entries."""
    return await DLQService.list_dlq(db, skip=skip, limit=limit)


@router.post("/{entry_id}/replay", response_model=DLQEntryResponse)
async def replay_job(entry_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> DLQEntryResponse:
    """Replay a failed job from the DLQ."""
    return await DLQService.replay_job(db, entry_id)
