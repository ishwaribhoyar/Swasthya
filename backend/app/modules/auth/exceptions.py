"""
Exceptions for the auth module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class AuthError(ClinIQBaseException):
    """Base exception for auth."""
    pass
