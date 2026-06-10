import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SentEmailResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    recipient: str
    subject: str
    body: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SentEmailListResponse(BaseModel):
    emails: list[SentEmailResponse]
    total: int
