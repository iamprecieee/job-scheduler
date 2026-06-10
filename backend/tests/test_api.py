import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus


@pytest.mark.asyncio
async def test_create_job(async_client: AsyncClient, db_session: AsyncSession) -> None:
    response = await async_client.post(
        "/api/v1/jobs",
        json={
            "type": "send_email",
            "priority": 1,
            "payload": {"to": "test@example.com"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["type"] == "send_email"
    assert data["priority"] == 1
    assert data["status"] == "pending"
    assert data["retry_count"] == 0
    assert data["payload"] == {"to": "test@example.com"}

    # Verify it was saved to DB
    job_id = data["id"]
    await db_session.rollback()  # Refresh transaction state
    job = await db_session.get(Job, uuid.UUID(job_id))
    assert job is not None
    assert job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_create_job_invalid_priority(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/jobs",
        json={
            "type": "send_email",
            "priority": 99,  # invalid
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_jobs(async_client: AsyncClient) -> None:
    # Create a couple of jobs
    await async_client.post(
        "/api/v1/jobs",
        json={"type": "send_email", "priority": 1, "payload": {}},
    )
    await async_client.post(
        "/api/v1/jobs",
        json={"type": "send_email", "priority": 2, "payload": {}},
    )

    response = await async_client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["jobs"]) == 2

    types = {item["type"] for item in data["jobs"]}
    assert "send_email" in types


@pytest.mark.asyncio
async def test_cancel_job(async_client: AsyncClient, db_session: AsyncSession) -> None:
    # Create job
    response = await async_client.post(
        "/api/v1/jobs",
        json={"type": "send_email", "priority": 1, "payload": {}},
    )
    job_id = response.json()["id"]

    # Cancel job
    cancel_response = await async_client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert cancel_response.status_code == 200

    # Verify status
    data = cancel_response.json()
    assert data["status"] == "cancelled"

    # DB verification
    await db_session.rollback()  # Refresh transaction state
    job = await db_session.get(Job, uuid.UUID(job_id))
    assert job.status == JobStatus.CANCELLED
