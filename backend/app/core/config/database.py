"""
Database configuration helpers.
"""
from __future__ import annotations
from app.core.config.settings import get_settings

def get_database_url() -> str:
    """Get the configured database URL."""
    return get_settings().DATABASE_URL
