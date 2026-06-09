"""Async request-scoped context propagation via contextvars.

Each incoming HTTP request gets a unique context dict (request_id, client_ip,
method, path, etc.) that is automatically attached to every log line emitted
during that request's lifetime — without passing context objects through the
call stack.

How it works:
    contextvars.ContextVar stores a per-task value in asyncio. When a new
    request arrives, the middleware creates a RequestContextLogger context
    manager that sets the ContextVar for the duration of the request. The
    Loguru patcher in setup.py reads this ContextVar and merges it into the
    log record's `extra` dict.
"""

import contextvars
import uuid
from typing import Any, Self

request_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "request_context", default=None
)


class RequestContextLogger:
    def __init__(self, request_id: str | None = None, **context: Any) -> None:
        self.request_id = request_id or uuid.uuid7().hex[:8]
        self.context: dict[str, Any] = {"request_id": self.request_id, **context}
        self._token: contextvars.Token[dict[str, Any] | None] | None = None

    async def __aenter__(self) -> Self:
        self._token = request_context.set(self.context)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._token is not None:
            request_context.reset(self._token)
            self._token = None
