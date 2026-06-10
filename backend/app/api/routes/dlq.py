import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.rate_limiter import limiter
from app.schemas.dlq import DLQEntryResponse, DLQListResponse
from app.services import DLQService

router = APIRouter(prefix="/dlq", tags=["DLQ"])


@router.get(
    "",
    response_model=DLQListResponse,
    summary="List Dead Letter Queue entries",
    description=(
        "Fetch a paginated list of jobs that have exhausted their retry limits and "
        "were permanently moved to the Dead Letter Queue (DLQ). Includes the specific "
        "exception stack trace that caused the failure."
    ),
)
@limiter.limit("120/minute")
async def list_dlq(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> DLQListResponse:
    return await DLQService.list_dlq(db, skip=skip, limit=limit)


@router.post(
    "/{entry_id}/replay",
    response_model=DLQEntryResponse,
    summary="Replay a failed job",
    description=(
        "Manually triggers a replay for a specific failed job in the DLQ. "
        "This will move the job out of the DLQ, reset its retry counter to 0, "
        "and set its status back to `PENDING` so the workers can pick it up again."
    ),
    responses={
        404: {"description": "DLQ entry not found."},
    },
)
@limiter.limit("60/minute")
async def replay_job(
    request: Request, entry_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> DLQEntryResponse:
    return await DLQService.replay_job(db, entry_id)
