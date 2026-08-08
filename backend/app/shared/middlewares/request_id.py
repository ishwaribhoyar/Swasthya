"""
Request ID middleware.
"""
from __future__ import annotations
import uuid
from fastapi import Request
from typing import Callable, Awaitable
from starlette.responses import Response

async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Add X-Request-ID header to responses."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
