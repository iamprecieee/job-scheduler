from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import verify_admin_token
from app.scheduler.benchmark import run_all_benchmarks

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


@router.get("", response_model=list[dict[str, Any]], dependencies=[Depends(verify_admin_token)])
def run_benchmark() -> list[dict[str, Any]]:
    """Execute performance benchmarks across all queue implementations."""
    return run_all_benchmarks()
