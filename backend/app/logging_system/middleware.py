import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.logging_system.context import RequestContextLogger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that instruments every HTTP request with structured logging.

    Buffers the response body only when status >= 400 so error detail appears
    in the server log alongside the status code.
    """

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
            status_code = response.status_code

            if not is_health or status_code >= 400:
                level = "WARNING" if status_code >= 400 else "INFO"

                if status_code >= 400:
                    body_bytes = b""
                    async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                        body_bytes += chunk if isinstance(chunk, bytes) else chunk.encode()

                    try:
                        import json

                        detail = json.loads(body_bytes).get(
                            "detail", body_bytes.decode(errors="replace")
                        )
                    except Exception:
                        detail = body_bytes.decode(errors="replace")

                    logger.log(
                        level,
                        "← {} {} {} {:.2f}ms | {}",
                        method,
                        path,
                        status_code,
                        duration,
                        detail,
                    )
                    response = StarletteResponse(
                        content=body_bytes,
                        status_code=status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
                else:
                    logger.log(level, "← {} {} {} {:.2f}ms", method, path, status_code, duration)

            response.headers["X-Request-ID"] = request_id
            return response
