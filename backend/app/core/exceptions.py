"""
Custom exception hierarchy for ClinIQ.
Maps domain exceptions directly to standard HTTP status codes.
"""
from __future__ import annotations

class ClinIQBaseException(Exception):
    """Base exception for all ClinIQ errors."""
    status_code: int = 400

class NotFoundError(ClinIQBaseException):
    """Resource not found."""
    status_code: int = 404

class UnauthorizedError(ClinIQBaseException):
    """Authentication failed or missing."""
    status_code: int = 401

class ForbiddenError(ClinIQBaseException):
    """Insufficient permissions."""
    status_code: int = 403

class ValidationError(ClinIQBaseException):
    """Data validation failed."""
    status_code: int = 422

class ConflictError(ClinIQBaseException):
    """Resource conflict."""
    status_code: int = 409

class InternalError(ClinIQBaseException):
    """Internal server error."""
    status_code: int = 500
