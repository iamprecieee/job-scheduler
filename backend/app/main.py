import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.routes import api_router
from app.config import settings
from app.logging_system.middleware import RequestLoggingMiddleware
from app.logging_system.setup import setup_logging
from app.scheduler.worker import aging_loop, db_sync_loop, worker_loop
from app.services.alert_service import alert_loop


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    setup_logging(log_level=settings.log_level)

    worker_task = asyncio.create_task(worker_loop())
    sync_task = asyncio.create_task(db_sync_loop())
    aging_task = asyncio.create_task(aging_loop())
    alert_task = asyncio.create_task(alert_loop())

    yield

    worker_task.cancel()

    sync_task.cancel()
    aging_task.cancel()
    alert_task.cancel()

    try:
        await asyncio.gather(
            worker_task,
            sync_task,
            aging_task,
            alert_task,
            return_exceptions=True,
        )
    except asyncio.CancelledError:
        pass


tags_metadata = [
    {
        "name": "Jobs",
        "description": "Manage background jobs' lifecycle - creation, cancellation, retrieval.",
    },
    {
        "name": "DLQ",
        "description": "Dead Letter Queue management for jobs with exhaausted retry limits.",
    },
    {
        "name": "Metrics",
        "description": "Real-time metrics and Server-Sent Events (SSE) for dashboard monitoring.",
    },
]

app = FastAPI(
    title="Job Scheduler API",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url=f"{settings.api_v1_str}/docs",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    redoc_url=f"{settings.api_v1_str}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


register_exception_handlers(app)
