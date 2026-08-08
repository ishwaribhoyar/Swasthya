"""
Custom exception hierarchy for Swasthya.
Maps domain exceptions directly to standard HTTP status codes.
"""
from __future__ import annotations

class SwasthyaBaseException(Exception):
    """Base exception for all Swasthya errors."""
    status_code: int = 400

class NotFoundError(SwasthyaBaseException):
    """Resource not found."""
    status_code: int = 404

class UnauthorizedError(SwasthyaBaseException):
    """Authentication failed or missing."""
    status_code: int = 401

class ForbiddenError(SwasthyaBaseException):
    """Insufficient permissions."""
    status_code: int = 403

class ValidationError(SwasthyaBaseException):
    """Data validation failed."""
    status_code: int = 422

class ConflictError(SwasthyaBaseException):
    """Resource conflict."""
    status_code: int = 409

# Backward compatibility alias
ClinIQBaseException = SwasthyaBaseException

class InternalError(SwasthyaBaseException):
    """Internal server error."""
    status_code: int = 500
