"""
Common standardized API envelope schemas.
"""
from __future__ import annotations
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized successful API response wrapper."""
    success: bool = True
    message: str = "Success"
    data: T
    request_id: Optional[str] = None

class ErrorDetail(BaseModel):
    """Field or validation error detail."""
    loc: Optional[list[str]] = None
    msg: str
    type: Optional[str] = None

class APIErrorResponse(BaseModel):
    """Standardized error API response wrapper."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[Any] = None
    request_id: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    timestamp: str
