"""
Pydantic schemas for ClinIQ Phase 5 Grounded RAG & AI Copilot.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceAttribution(BaseModel):
    """Clickable evidence source attribution metadata."""
    model_config = ConfigDict(from_attributes=True)

    record_id: str
    title: str
    event_date: str
    document_type: str


class AmbiguousCandidate(BaseModel):
    """Patient option returned when name lookup matches multiple patients."""
    id: str
    mrn: str
    name: str
    date_of_birth: str
    gender: str


class AICopilotChatRequest(BaseModel):
    """Request payload for POST /api/v1/ai-copilot/chat."""
    message: str = Field(..., min_length=2, max_length=2000, description="Clinician query message")
    patient_id: Optional[str] = Field(None, description="Optional patient UUID when in patient-scoped mode")
    conversation_id: Optional[str] = Field(None, description="Optional conversation context ID")


class RAGAuditTrace(BaseModel):
    """Stage-by-stage execution trace for auditability."""
    intent: str
    retrieval_pathway: str
    sources_count: int
    confidence: str
    grounding_passed: bool
    medical_safety_passed: bool


class AICopilotChatResponse(BaseModel):
    """Unified response container for ClinIQ AI Copilot."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    answer: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW, INSUFFICIENT
    intent: str = "PATIENT_SUMMARY"
    sources: List[SourceAttribution] = []
    is_general_info: bool = False
    ambiguous_candidates: List[AmbiguousCandidate] = []
    audit_trace: Optional[RAGAuditTrace] = None
    disclaimer: str = "ClinIQ provides record-grounded clinical information and does not replace clinician judgment."
