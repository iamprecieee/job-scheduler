import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import ErrorResponse


async def _handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    if not errors:
        detail = "Validation error"
    else:
        err = errors[0]
        loc_parts = [str(p) for p in err["loc"] if p != "body"]
        loc = " → ".join(loc_parts)
        msg = err["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        elif ":" in msg:
            msg = msg.split(":")[-1].strip()
        if msg:
            msg = msg[0].lower() + msg[1:]
        detail = f"{loc}: {msg}" if loc else msg.capitalize()

    logger.warning("Validation error on {} {}: {}", request.method, request.url.path, detail)
    return JSONResponse(status_code=422, content=ErrorResponse(detail=detail).model_dump())


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Log server-side faults; client errors (4xx) are at DEBUG to avoid noise.
    level = "ERROR" if exc.status_code >= 500 else "DEBUG"
    logger.log(
        level,
        "HTTP {} on {} {}: {}",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=str(exc.detail)).model_dump(),
    )


async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    tb = traceback.extract_tb(exc.__traceback__)
    tb_str = "".join(traceback.format_list(tb)) if tb else "No traceback available"
    logger.opt(exception=True).critical(
        "Unhandled exception on {} {}: {}\n{}",
        request.method,
        request.url.path,
        exc,
        tb_str,
    )
    return JSONResponse(
        status_code=500, content=ErrorResponse(detail="Internal server error").model_dump()
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _handle_request_validation)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unhandled)
