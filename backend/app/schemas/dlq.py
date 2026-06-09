import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.job import JobResponse


class DLQEntryResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    failure_reason: str
    entered_at: datetime
    retry_attempted_at: datetime | None

    job: JobResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class DLQListResponse(BaseModel):
    entries: list[DLQEntryResponse]
    total: int
