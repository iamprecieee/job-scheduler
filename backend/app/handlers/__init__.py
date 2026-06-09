from typing import Any, Protocol, runtime_checkable

from app.handlers.email_handler import EmailHandler
from app.handlers.registry import get_handler, register_handler


@runtime_checkable
class JobHandler(Protocol):
    """Protocol every job handler must satisfy."""

    async def execute(self, payload: dict[str, Any]) -> None: ...


__all__ = [
    "JobHandler",
    "EmailHandler",
    "get_handler",
    "register_handler",
]
