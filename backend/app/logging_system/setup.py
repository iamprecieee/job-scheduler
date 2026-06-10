import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.logging_system.context import request_context


class LogFormat:
    """Provides formatting strings for console and file sinks."""

    @staticmethod
    def console_format(record: Any) -> str:
        return (
            "<dim>{time:YYYY-MM-DD HH:mm:ss.SSS}</dim> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - "
            "<level>{message}</level>\n"
        )

    @staticmethod
    def json_format(record: Any) -> str:
        return "{message}\n"


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Walk the call stack to find the original call site
        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        ctx = request_context.get() or {}
        (
            logger.opt(depth=depth, exception=record.exc_info)
            .bind(**ctx)
            .log(level, record.getMessage())
        )


def _context_patcher(record: Any) -> None:
    ctx = request_context.get()
    if ctx:
        record["extra"].update(ctx)


def setup_logging(
    log_level: str = "INFO",
    log_file_path: str = "logs/app.log",
    environment: str = "development",
) -> None:
    is_local = environment.lower() in {"local", "dev", "development"}
    log_file = Path(log_file_path)

    # Reset: remove default Loguru handler, install InterceptHandler on stdlib root
    logger.remove()

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    logging.root.setLevel(log_level)

    # Redirect all library loggers to propagate through InterceptHandler
    for name in list(logging.root.manager.loggerDict):
        lib_logger = logging.getLogger(name)
        lib_logger.handlers = []
        lib_logger.propagate = True

    # Suppress duplicate uvicorn access logs (our middleware logs requests)
    logging.getLogger("uvicorn.access").propagate = False

    # Sink 1: stdout
    logger.add(
        sys.stdout,
        level=log_level,
        colorize=is_local,
        serialize=not is_local,
        backtrace=is_local,
        diagnose=is_local,  # Never leak variable values in production
        format=LogFormat.console_format if is_local else LogFormat.json_format,
    )

    # Ensure log directories exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    error_log_file = log_file.with_name(f"{log_file.stem}_errors{log_file.suffix}")

    # Sink 2: info file (structured, thread-safe, rotated, compressed)
    logger.add(
        str(log_file),
        level="INFO",
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        serialize=True,
    )

    # Sink 3: error file (longer retention for post-mortems)
    logger.add(
        str(error_log_file),
        level="ERROR",
        rotation="10 MB",
        retention="60 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        serialize=True,
    )

    # Attach context patcher so request-scoped fields appear in every log
    logger.configure(patcher=_context_patcher)
    logger.info("Logging initialized | env={}", environment)
