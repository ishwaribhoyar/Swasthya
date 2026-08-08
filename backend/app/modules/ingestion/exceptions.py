"""
Exceptions for the ingestion module.
"""
from __future__ import annotations
from app.core.exceptions import SwasthyaBaseException

class IngestionError(SwasthyaBaseException):
    """Base exception for ingestion."""
    pass
