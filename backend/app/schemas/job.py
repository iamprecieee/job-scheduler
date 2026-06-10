import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobStatus


class CreateJobRequest(BaseModel):
    type: Literal["send_email"] = Field(..., description="Job handler type (e.g. 'send_email')")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON payload for the job",
        json_schema_extra={
            "example": {
                "to": "test@example.com",
                "subject": "Hello Background Worker",
                "body": "This is a test email sent from the Job Scheduler!",
            }
        },
    )
    priority: Literal[1, 2, 3] = Field(..., description="1 (High), 2 (Medium), 3 (Low)")

    scheduled_at: datetime | None = Field(
        None, description="Run at specific future time (ISO format)"
    )
    recurring_interval: Literal["every_1_minute", "every_5_minutes", "every_1_hour"] | None = Field(
        None,
        description="Optional recurring schedule",
    )
    dependencies: list[uuid.UUID] = Field(
        default_factory=list, description="List of job IDs that must complete first"
    )


class JobResponse(BaseModel):
    id: uuid.UUID
    type: str
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
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
