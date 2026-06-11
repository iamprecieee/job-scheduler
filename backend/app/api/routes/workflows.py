from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.api.rate_limiter import limiter
from app.schemas.workflow import CreateWorkflowRequest, WorkflowResponse
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new DAG workflow",
    description="Creates a workflow blueprint containing multiple jobs and dependencies.",
)
@limiter.limit("30/minute")
async def create_workflow(
    request: Request, workflow_request: CreateWorkflowRequest, db: AsyncSession = Depends(get_db)
) -> WorkflowResponse:
    return await WorkflowService.create_workflow(db, workflow_request)


@router.get(
    "",
    response_model=list[WorkflowResponse],
    summary="List all workflows",
    description="Retrieve a list of all defined DAG workflows.",
)
@limiter.limit("120/minute")
async def list_workflows(
    request: Request, db: AsyncSession = Depends(get_db)
) -> list[WorkflowResponse]:
    return await WorkflowService.list_workflows(db)
