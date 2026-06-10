import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.rate_limiter import limiter
from app.handlers import get_handler
from app.models import JobStatus
from app.schemas.job import CreateJobRequest, JobListResponse, JobResponse
from app.services import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new background job",
    description=(
        "Submits a new job to the background scheduler. The `type` must be registered "
        "in the system (e.g., `send_email`). You can provide `dependencies` to create a "
        "DAG execution workflow, or `scheduled_at` to delay execution."
    ),
    responses={
        201: {"description": "Job created successfully."},
        422: {"description": "Invalid job type or validation error."},
    },
)
@limiter.limit("30/minute")
async def create_job(
    request: Request, job_request: CreateJobRequest, db: AsyncSession = Depends(get_db)
) -> JobResponse:
    try:
        get_handler(job_request.type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return await JobService.create_job(db, job_request)


@router.get(
    "",
    response_model=JobListResponse,
    summary="List and filter jobs",
    description=(
        "Retrieve a paginated list of jobs. You can optionally filter the results "
        "by selecting a specific `status` from dropdown (e.g., `completed`, `pending`, `failed`)."
    ),
)
@limiter.limit("120/minute")
async def list_jobs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: JobStatus | None = Query(
        None, alias="status", description="Filter by job status"
    ),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    return await JobService.list_jobs(
        db, skip=skip, limit=limit, status=status_filter.value if status_filter else None
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Retrieve job details",
    description="Fetch complete state, payload, and retry history of a specific job by its UUID.",
    responses={
        404: {"description": "Job not found."},
    },
)
@limiter.limit("120/minute")
async def get_job(
    request: Request, job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> JobResponse:
    return await JobService.get_job(db, job_id)


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    summary="Cancel a pending job",
    description=(
        "Soft-cancels a job. If the job is already `processing`, the worker will gracefully "
        "halt execution if cooperative cancellation is implemented by the handler. If the job "
        "is already completed or failed, this returns a 400 error."
    ),
    responses={
        400: {"description": "Job cannot be cancelled (already completed/failed)."},
        404: {"description": "Job not found."},
    },
)
@limiter.limit("60/minute")
async def cancel_job(
    request: Request, job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> JobResponse:
    return await JobService.cancel_job(db, job_id)
