"""
Exceptions for the analytics module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class AnalyticsError(ClinIQBaseException):
    """Base exception for analytics."""
    pass
