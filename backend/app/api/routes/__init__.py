from fastapi import APIRouter

from app.api.routes.benchmark import router as benchmark_router
from app.api.routes.dlq import router as dlq_router
from app.api.routes.inbox import router as inbox_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.sse import router as sse_router
from app.api.routes.workflows import router as workflows_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(workflows_router)
api_router.include_router(dlq_router)
api_router.include_router(inbox_router)
api_router.include_router(sse_router)
api_router.include_router(benchmark_router)
