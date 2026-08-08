"""
Exceptions for the ingestion module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class IngestionError(ClinIQBaseException):
    """Base exception for ingestion."""
    pass
