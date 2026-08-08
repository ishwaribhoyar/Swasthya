"""
Pydantic schemas for AI Copilot RAG queries and audit responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceCitationSchema(BaseModel):
    """Source document citation schema."""

    doc_id: str
    filename: str
    category: str
    header: str
    snippet: str
    relevance_score: float


class AIQueryRequest(BaseModel):
    """Body for POST /ai-copilot/query — run RAG reasoning for a patient."""

    patient_id: str = Field(..., description="UUID of target patient")
    query: str = Field(..., min_length=2, max_length=2000, description="Clinician question")


class AIQueryResponse(BaseModel):
    """Response object containing clinical reasoning answer, citations, confidence, and audit hash."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    query: str
    answer: str
    confidence_score: float
    sources: List[SourceCitationSchema]
    audit_hash: str
    created_at: datetime
