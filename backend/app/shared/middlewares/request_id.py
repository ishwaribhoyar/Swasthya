"""
Request ID and CORS Preflight middleware.
Guarantees X-Request-ID and CORS headers on every response, including errors and preflights.
"""
from __future__ import annotations
import uuid
from typing import Callable, Awaitable
from fastapi import Request
from starlette.responses import Response


async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Handle preflights, add X-Request-ID, and guarantee CORS headers on responses."""
    origin = request.headers.get("origin", "*")

    if request.method == "OPTIONS":
        response = Response(status_code=204)
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    try:
        response = await call_next(request)
    except Exception:
        response = Response(
            content='{"success": false, "message": "Internal Server Error"}',
            status_code=500,
            media_type="application/json",
        )

    response.headers["X-Request-ID"] = request_id
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response
