import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.handlers import get_handler
from app.schemas.job import CreateJobRequest, JobListResponse, JobResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(request: CreateJobRequest, db: AsyncSession = Depends(get_db)) -> JobResponse:
    """Create a new job. Validates job type against the handler registry before persisting."""
    try:
        get_handler(request.type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return await JobService.create_job(db, request)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List all jobs with pagination and optional status filter."""
    return await JobService.list_jobs(db, skip=skip, limit=limit, status=status_filter)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobResponse:
    """Get a specific job by ID."""
    return await JobService.get_job(db, job_id)


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobResponse:
    """Cancel a pending job."""
    return await JobService.cancel_job(db, job_id)
