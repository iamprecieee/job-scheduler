import asyncio
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from loguru import logger
from sse_starlette.sse import EventSourceResponse

from app.scheduler.worker import job_queue

router = APIRouter(prefix="/sse", tags=["Events"])


async def event_generator(request: Request) -> AsyncGenerator[dict[str, str]]:
    """Generate SSE events for queue length."""
    while True:
        if await request.is_disconnected():
            logger.info("SSE client disconnected")
            break

        queue_len = len(job_queue)

        yield {"event": "queue_status", "data": f'{{"queue_length": {queue_len}}}'}

        await asyncio.sleep(2.0)


@router.get("/queue")
async def queue_events(request: Request) -> EventSourceResponse:
    """Server-Sent Events endpoint for real-time queue monitoring."""
    return EventSourceResponse(event_generator(request))
