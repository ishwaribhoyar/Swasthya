"""
General helper utilities.
"""
from __future__ import annotations
import uuid
import re
from datetime import datetime, timezone

def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    """Generate a string UUID."""
    return str(uuid.uuid4())

def slugify(text: str) -> str:
    """Convert text to a slugified string."""
    return re.sub(r'[^\w\-]', '', text.lower().replace(' ', '-'))

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length."""
    return text[:max_length] + '...' if len(text) > max_length else text
