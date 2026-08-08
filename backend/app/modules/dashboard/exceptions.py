"""
Exceptions for the dashboard module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class DashboardError(ClinIQBaseException):
    """Base exception for dashboard."""
    pass
