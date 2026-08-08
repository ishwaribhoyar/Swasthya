"""
Exceptions for the patients module.
"""
from __future__ import annotations
from app.core.exceptions import SwasthyaBaseException

class PatientsError(SwasthyaBaseException):
    """Base exception for patients."""
    pass
