import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


class CreateJobRequest(BaseModel):
    type: str = Field(..., max_length=100, description="Job handler type (e.g. 'send_email')")
    payload: dict[str, Any] = Field(default_factory=dict, description="JSON payload for the job")
    priority: int = Field(..., ge=1, le=3, description="1 (High), 2 (Medium), 3 (Low)")

    scheduled_at: datetime | None = Field(None, description="Run at specific future time")
    recurring_interval: str | None = Field(
        None,
        pattern="^(every_1_minute|every_5_minutes|every_1_hour)$",
        description="Optional recurring schedule",
    )
    dependencies: list[uuid.UUID] = Field(
        default_factory=list, description="List of job IDs that must complete first"
    )


class JobResponse(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    priority: int
    effective_priority: float
    status: JobStatus
    retry_count: int
    scheduled_at: datetime | None
    recurring_interval: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
