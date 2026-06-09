from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by all exception handlers."""

    detail: str
