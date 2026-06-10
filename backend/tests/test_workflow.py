import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session_factory
from app.models import DeadLetterEntry, Job, JobDependency, JobStatus
from app.scheduler.worker import process_job


@pytest.fixture
def mock_handler_success(monkeypatch):
    class MockHandler:
        async def execute(self, payload):
            return {"status": "success"}

    monkeypatch.setattr("app.scheduler.worker.get_handler", lambda type: MockHandler())


@pytest.fixture
def mock_handler_failure(monkeypatch):
    class MockHandler:
        async def execute(self, payload):
            raise ValueError("Intentional failure")

    monkeypatch.setattr("app.scheduler.worker.get_handler", lambda type: MockHandler())


@pytest.mark.asyncio
async def test_dag_dependencies(db_session: AsyncSession, mock_handler_success) -> None:
    # Create parent job
    parent_job = Job(type="send_email", priority=1, effective_priority=1.0)
    db_session.add(parent_job)
    await db_session.flush()

    # Create child job
    child_job = Job(type="send_email", priority=1, effective_priority=1.0)
    db_session.add(child_job)
    await db_session.flush()

    # Add dependency
    dep = JobDependency(job_id=child_job.id, depends_on_job_id=parent_job.id)
    db_session.add(dep)
    await db_session.commit()

    # Process child first - should not complete because parent is pending
    await process_job(child_job.id)

    # Refresh child status
    async with async_session_factory() as session:
        child = await session.get(Job, child_job.id)
        assert child.status == JobStatus.PENDING

    # Process parent - should complete
    await process_job(parent_job.id)

    async with async_session_factory() as session:
        parent = await session.get(Job, parent_job.id)
        assert parent.status == JobStatus.COMPLETED

    # Process child again - should complete now
    await process_job(child_job.id)

    async with async_session_factory() as session:
        child = await session.get(Job, child_job.id)
        assert child.status == JobStatus.COMPLETED


@pytest.mark.asyncio
async def test_retry_logic(db_session: AsyncSession, mock_handler_failure) -> None:
    job = Job(type="send_email", priority=1, effective_priority=1.0)
    db_session.add(job)
    await db_session.commit()

    # Process job - it should fail
    await process_job(job.id)

    async with async_session_factory() as session:
        job_updated = await session.get(Job, job.id)
        assert job_updated.status == JobStatus.PENDING
        assert job_updated.retry_count == 1
        assert "Intentional failure" in job_updated.error_message


@pytest.mark.asyncio
async def test_dlq_logic(db_session: AsyncSession, mock_handler_failure) -> None:
    job = Job(type="send_email", priority=1, effective_priority=1.0)
    db_session.add(job)
    await db_session.commit()

    # Process job repeatedly until it hits DLQ
    max_retries = settings.max_retries
    for _ in range(max_retries + 1):
        await process_job(job.id)

    async with async_session_factory() as session:
        job_updated = await session.get(Job, job.id)

        # After exceeding max_retries, it should be FAILED
        assert job_updated.status == JobStatus.FAILED
        assert job_updated.retry_count == max_retries + 1

        # Check DLQ entry
        stmt = select(DeadLetterEntry).where(DeadLetterEntry.job_id == job.id)
        result = await session.execute(stmt)
        dlq_entry = result.scalar_one_or_none()

        assert dlq_entry is not None
        assert "Intentional failure" in dlq_entry.failure_reason
