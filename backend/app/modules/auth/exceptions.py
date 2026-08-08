"""
Exceptions for the auth module.
"""
from __future__ import annotations
from app.core.exceptions import SwasthyaBaseException

class AuthError(SwasthyaBaseException):
    """Base exception for auth."""
    pass
