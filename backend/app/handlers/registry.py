from typing import Any

from app.handlers.email_handler import EmailHandler

# Concrete mapping — populated at import time so it is available before any
# worker coroutine executes. Using a dict keeps lookup O(1) and makes
# the full set of supported types introspectable at runtime.
_REGISTRY: dict[str, type] = {
    "send_email": EmailHandler,
}


def register_handler(job_type: str, handler_cls: type) -> None:
    if job_type in _REGISTRY:
        raise ValueError(
            f"Handler for job type '{job_type}' is already registered as {_REGISTRY[job_type]!r}"
        )
    _REGISTRY[job_type] = handler_cls


def get_handler(job_type: str) -> Any:
    handler_cls = _REGISTRY.get(job_type)
    if handler_cls is None:
        supported = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown job type '{job_type}'. Supported types: {supported}")
    return handler_cls()
