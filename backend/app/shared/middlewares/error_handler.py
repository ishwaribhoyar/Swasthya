"""
Global error handler middleware with guaranteed CORS headers and standard APIErrorResponse envelope.
"""
from __future__ import annotations

from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import ClinIQBaseException
from app.observability.logger import get_logger

logger = get_logger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Extract X-Request-ID if present."""
    return request.headers.get("X-Request-ID")


def _add_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    """Ensure CORS headers are present on error responses."""
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


async def global_error_handler(request: Request, exc: ClinIQBaseException) -> JSONResponse:
    """Handle custom application exceptions globally with standard envelope."""
    status_code = getattr(exc, "status_code", 400)
    logger.error("app_error", error=str(exc), status_code=status_code)
    response = JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": str(exc),
            "error_code": exc.__class__.__name__,
            "details": str(exc),
            "request_id": _get_request_id(request),
        },
    )
    return _add_cors_headers(request, response)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions with standard envelope."""
    logger.error("http_error", error=exc.detail, status_code=exc.status_code)
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error_code": "HTTPException",
            "details": str(exc.detail),
            "request_id": _get_request_id(request),
        },
        headers=exc.headers,
    )
    return _add_cors_headers(request, response)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with standard envelope."""
    logger.error("validation_error", error=str(exc.errors()))
    
    # Safely serialize Pydantic v2 errors
    safe_errors = []
    for error in exc.errors():
        error_copy = error.copy()
        if "ctx" in error_copy:
            error_copy["ctx"] = {k: str(v) for k, v in error_copy["ctx"].items()}
        safe_errors.append(error_copy)

    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Input validation failed.",
            "error_code": "ValidationError",
            "details": safe_errors,
            "request_id": _get_request_id(request),
        },
    )
    return _add_cors_headers(request, response)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled 500 exceptions with standard envelope and guaranteed CORS headers."""
    logger.exception("unhandled_server_error", error=str(exc))
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "error_code": "InternalServerError",
            "details": str(exc),
            "request_id": _get_request_id(request),
        },
    )
    return _add_cors_headers(request, response)
