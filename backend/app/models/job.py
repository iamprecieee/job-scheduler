import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class JobStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)
    type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Priority: 1 (High), 2 (Medium), 3 (Low)
    priority: Mapped[int] = mapped_column(SmallInteger, index=True)
    effective_priority: Mapped[float] = mapped_column(Float, index=True)

    status: Mapped[JobStatus] = mapped_column(String, default=JobStatus.PENDING, index=True)
    retry_count: Mapped[int] = mapped_column(SmallInteger, default=0)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    recurring_interval: Mapped[str | None] = mapped_column(String(20))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    error_message: Mapped[str | None] = mapped_column(Text)

    # Relationships are defined via back_populates in other models.
    # dependency tracking and DLQ tracking
