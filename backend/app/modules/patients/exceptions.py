"""
Exceptions for the patients module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class PatientsError(ClinIQBaseException):
    """Base exception for patients."""
    pass
