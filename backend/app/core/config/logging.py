"""
Logging configuration using structlog.
"""
from __future__ import annotations
import structlog

def configure_logging() -> None:
    """Configure structlog for the application."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
