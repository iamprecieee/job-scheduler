import time
import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers import get_handler
from app.models.dependency import JobDependency
from app.models.job import Job, JobStatus
from app.models.workflow import Workflow, WorkflowNode, WorkflowNodeDependency
from app.scheduler import job_queue
from app.schemas.workflow import CreateWorkflowRequest, WorkflowNodeResponse, WorkflowResponse


class WorkflowService:
    @staticmethod
    async def create_workflow(
        session: AsyncSession, request: CreateWorkflowRequest
    ) -> WorkflowResponse:
        # Validate all job types before inserting anything
        for node in request.nodes:
            try:
                get_handler(node.type)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc

        # Create workflow root
        workflow = Workflow(
            name=request.name,
            scheduled_at=request.scheduled_at,
            recurring_interval=request.recurring_interval,
        )
        session.add(workflow)
        await session.flush()

        client_to_node_id: dict[str, uuid.UUID] = {}
        nodes_to_insert: list[WorkflowNode] = []

        # First pass: create all nodes and generate UUIDs
        for node_req in request.nodes:
            new_node_id = uuid.uuid7()
            client_to_node_id[node_req.client_id] = new_node_id

            node_model = WorkflowNode(
                id=new_node_id,
                workflow_id=workflow.id,
                client_id=node_req.client_id,
                type=node_req.type,
                payload=node_req.payload,
                priority=node_req.priority,
            )
            nodes_to_insert.append(node_model)
            session.add(node_model)

        await session.flush()

        # Second pass: map dependencies
        for node_req in request.nodes:
            src_node_id = client_to_node_id[node_req.client_id]

            for dep_client_id in node_req.dependencies:
                if dep_client_id not in client_to_node_id:
                    await session.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Dependency '{dep_client_id}' not found in provided nodes.",
                    )

                dest_node_id = client_to_node_id[dep_client_id]

                dep_model = WorkflowNodeDependency(
                    node_id=src_node_id, depends_on_node_id=dest_node_id
                )
                session.add(dep_model)

        # Build an adjacency list for cycle detection
        adj_list: dict[str, list[str]] = {node_req.client_id: [] for node_req in request.nodes}
        for node_req in request.nodes:
            # node_req.dependencies contains the IDs of nodes that this node depends on.
            # This means the edge is: dependency -> node
            for dep_client_id in node_req.dependencies:
                adj_list[dep_client_id].append(node_req.client_id)

        # Detect cycles using DFS
        visited = set()
        rec_stack = set()

        def is_cyclic(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in adj_list.get(node_id, []):
                if neighbor not in visited:
                    if is_cyclic(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in adj_list:
            if node_id not in visited:
                if is_cyclic(node_id):
                    await session.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Cycle detected in the workflow graph. "
                            "A workflow must be a Directed Acyclic Graph (DAG)."
                        ),
                    )

        old_id_to_new_job: dict[uuid.UUID, Job] = {}

        for node in nodes_to_insert:
            new_job = Job(
                type=node.type,
                payload=node.payload,
                priority=node.priority,
                effective_priority=float(node.priority),
                status=JobStatus.PENDING,
                retry_count=0,
                scheduled_at=workflow.scheduled_at,
            )
            session.add(new_job)
            old_id_to_new_job[node.id] = new_job

        await session.flush()

        # Create Job dependencies for this first run
        for node_req in request.nodes:
            src_node_id = client_to_node_id[node_req.client_id]
            new_node_job = old_id_to_new_job.get(src_node_id)

            for dep_client_id in node_req.dependencies:
                dest_node_id = client_to_node_id[dep_client_id]
                new_dep_job = old_id_to_new_job.get(dest_node_id)

                if new_node_job and new_dep_job:
                    job_dep = JobDependency(
                        job_id=new_node_job.id,
                        depends_on_job_id=new_dep_job.id,
                    )
                    session.add(job_dep)

        # Push to in-memory queue
        for new_job in old_id_to_new_job.values():
            scheduled_ts = new_job.scheduled_at.timestamp() if new_job.scheduled_at else time.time()
            job_queue.push(str(new_job.id), new_job.effective_priority, scheduled_ts, time.time())

        # Advance workflow schedule to the next recurrence
        if workflow.recurring_interval:
            base_time = workflow.scheduled_at or request.scheduled_at
            if not base_time:
                # Fallback if no initial schedule was provided but recurring is set
                import datetime

                base_time = datetime.datetime.now(datetime.UTC)

            if workflow.recurring_interval == "every_1_minute":
                workflow.scheduled_at = base_time + timedelta(minutes=1)
            elif workflow.recurring_interval == "every_5_minutes":
                workflow.scheduled_at = base_time + timedelta(minutes=5)
            elif workflow.recurring_interval == "every_1_hour":
                workflow.scheduled_at = base_time + timedelta(hours=1)
        else:
            workflow.scheduled_at = None

        await session.commit()

        # Load relationships for response
        stmt = select(Workflow).where(Workflow.id == workflow.id)
        result = await session.execute(stmt)
        workflow_refreshed = result.scalar_one()

        # Manually assemble the response since we didn't add SQLAlchemy relationship() explicitly
        node_stmt = select(WorkflowNode).where(WorkflowNode.workflow_id == workflow.id)
        node_res = await session.execute(node_stmt)
        db_nodes = node_res.scalars().all()

        dep_stmt = select(WorkflowNodeDependency).where(
            WorkflowNodeDependency.node_id.in_([node.id for node in db_nodes])
        )
        dep_res = await session.execute(dep_stmt)
        db_deps = dep_res.scalars().all()

        node_deps_map = {node.id: [] for node in db_nodes}
        for dep in db_deps:
            # Map depends_on_node_id back to client_id for the response
            target_node = next(node for node in db_nodes if node.id == dep.depends_on_node_id)
            node_deps_map[dep.node_id].append(target_node.client_id)

        response = WorkflowResponse(
            id=workflow_refreshed.id,
            name=workflow_refreshed.name,
            scheduled_at=workflow_refreshed.scheduled_at,
            recurring_interval=workflow_refreshed.recurring_interval,
            created_at=workflow_refreshed.created_at,
            updated_at=workflow_refreshed.updated_at,
            nodes=[
                WorkflowNodeResponse(
                    id=node.id,
                    client_id=node.client_id,
                    type=node.type,
                    payload=node.payload,
                    priority=node.priority,
                    dependencies=node_deps_map[node.id],
                )
                for node in db_nodes
            ],
        )
        return response

    @staticmethod
    async def list_workflows(session: AsyncSession) -> list[WorkflowResponse]:
        stmt = select(Workflow).order_by(Workflow.created_at.desc())
        result = await session.execute(stmt)
        workflows = result.scalars().all()

        # Load all nodes and dependencies for these workflows
        workflow_ids = [workflow.id for workflow in workflows]
        if not workflow_ids:
            return []

        node_stmt = select(WorkflowNode).where(WorkflowNode.workflow_id.in_(workflow_ids))
        node_res = await session.execute(node_stmt)
        db_nodes = node_res.scalars().all()

        node_ids = [node.id for node in db_nodes]
        db_deps = []
        if node_ids:
            dep_stmt = select(WorkflowNodeDependency).where(
                WorkflowNodeDependency.node_id.in_(node_ids)
            )
            dep_res = await session.execute(dep_stmt)
            db_deps = dep_res.scalars().all()

        node_deps_map = {node.id: [] for node in db_nodes}
        for dep in db_deps:
            target_node = next(node for node in db_nodes if node.id == dep.depends_on_node_id)
            node_deps_map[dep.node_id].append(target_node.client_id)

        nodes_by_workflow = {workflow.id: [] for workflow in workflows}
        for node in db_nodes:
            nodes_by_workflow[node.workflow_id].append(
                WorkflowNodeResponse(
                    id=node.id,
                    client_id=node.client_id,
                    type=node.type,
                    payload=node.payload,
                    priority=node.priority,
                    dependencies=node_deps_map[node.id],
                )
            )

        responses = []
        for workflow in workflows:
            responses.append(
                WorkflowResponse(
                    id=workflow.id,
                    name=workflow.name,
                    scheduled_at=workflow.scheduled_at,
                    recurring_interval=workflow.recurring_interval,
                    created_at=workflow.created_at,
                    updated_at=workflow.updated_at,
                    nodes=nodes_by_workflow[workflow.id],
                )
            )
        return responses
