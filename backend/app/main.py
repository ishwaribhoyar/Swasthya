"""
Main FastAPI application factory and entry point.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.v1.router import api_router
from app.core.config.settings import get_settings
from app.core.exceptions import ClinIQBaseException
from app.database.init_db import init_db
from app.shared.middlewares.cors import configure_cors
from app.shared.middlewares.error_handler import (
    global_error_handler,
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.shared.middlewares.request_id import request_id_middleware
from app.shared.utils.helpers import utcnow


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events."""
    # Create SQLite database tables if they do not exist
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # Register custom HTTP middlewares FIRST
    app.middleware("http")(request_id_middleware)

    # Register CORS middleware LAST so it wraps as the outermost layer
    configure_cors(app)

    # Register custom exception handlers with guaranteed CORS headers
    app.add_exception_handler(ClinIQBaseException, global_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "version": settings.VERSION,
            "timestamp": utcnow().isoformat(),
        }

    return app


app = create_app()
