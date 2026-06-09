import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_system.context import RequestContextLogger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that instruments every HTTP request with structured logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = uuid.uuid7().hex
        client_host = request.client.host if request.client else "unknown"
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or client_host
        method = request.method
        path = request.url.path

        ctx = {
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "user_agent": request.headers.get("user-agent", ""),
        }

        async with RequestContextLogger(request_id=request_id, **ctx):
            is_health = path in {"/health", "/metrics"}
            if not is_health:
                logger.info("→ {} {}", method, path)

            start_time = time.perf_counter()
            try:
                response = await call_next(request)
            except Exception:
                duration = (time.perf_counter() - start_time) * 1000
                logger.error("✗ {} {} — failed after {:.2f}ms", method, path, duration)
                raise

            duration = (time.perf_counter() - start_time) * 1000
            level = "WARNING" if response.status_code >= 400 else "INFO"

            if not is_health or response.status_code >= 400:
                logger.log(
                    level, "← {} {} {} {:.2f}ms", method, path, response.status_code, duration
                )

            response.headers["X-Request-ID"] = request_id
            return response
