"""
Logger instantiation.
"""
from __future__ import annotations
import structlog
from typing import Any

def get_logger(name: str) -> Any:
    """Get a structured logger bound to a module name."""
    return structlog.get_logger().bind(module=name)
