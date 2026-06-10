from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.database
import app.scheduler.worker
from app.api.dependencies import get_db
from app.main import app as fastapi_app
from app.models.base import Base

# Use file-backed SQLite to ensure separate sessions see committed data correctly
TEST_DATABASE_URL = "sqlite+aiosqlite:///test_scheduler.db"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_session() -> AsyncGenerator[AsyncSession]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Override dependency for FastAPI routes
fastapi_app.dependency_overrides[get_db] = override_get_session

# Globally monkeypatch async_session_factory for background workers
app.database.async_session_factory = TestingSessionLocal


app.scheduler.worker.async_session_factory = TestingSessionLocal


@pytest.fixture(scope="session", autouse=True)
def anyio_backend():
    """Use asyncio for anyio."""
    return "asyncio"


@pytest.fixture(autouse=True)
async def db_setup_and_teardown():
    """Create and drop all tables before and after each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Provide an isolated database session for a test."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Provide an async test client connected to the FastAPI app."""

    @asynccontextmanager
    async def mock_lifespan(app):
        yield

    fastapi_app.router.lifespan_context = mock_lifespan

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
