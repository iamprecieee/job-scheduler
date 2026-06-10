import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.job import Job


class DeadLetterEntry(Base):
    __tablename__ = "dead_letters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid7)
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, index=True
    )
    failure_reason: Mapped[str] = mapped_column(Text)

    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    retry_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    job: Mapped[Job] = relationship("Job")
