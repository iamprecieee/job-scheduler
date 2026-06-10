import asyncio

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import get_db
from app.schemas.email import SentEmailListResponse
from app.services.email_service import EmailService, subscribe_inbox, unsubscribe_inbox

router = APIRouter(prefix="/inbox", tags=["Inbox"])


@router.get(
    "",
    response_model=SentEmailListResponse,
    summary="List sent emails",
    description=(
        "Returns a paginated list of all emails that were successfully sent by "
        "completed `send_email` jobs, ordered newest-first. Use this to browse "
        "the scheduler's outbound email history."
    ),
)
async def list_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> SentEmailListResponse:
    return await EmailService.list_emails(db, skip=skip, limit=limit)


@router.get(
    "/stream",
    summary="Real-time inbox stream (SSE)",
    description=(
        "Server-Sent Events endpoint that pushes a `new_email` event every time "
        "a `send_email` job completes successfully. Connect from the browser with "
        "`new EventSource('/api/v1/inbox/stream')` to receive live inbox updates."
    ),
)
async def inbox_stream(request: Request):
    queue = subscribe_inbox()

    async def event_generator():
        try:
            # Send an immediate connected event so the browser recognises the stream
            yield {"event": "connected", "data": "ok"}

            while True:
                if await request.is_disconnected():
                    break

                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "new_email", "data": data}
                except TimeoutError:
                    # Keepalive to prevent proxy/browser timeout
                    yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe_inbox(queue)

    return EventSourceResponse(event_generator())
