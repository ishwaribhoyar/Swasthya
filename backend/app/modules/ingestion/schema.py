"""
Ingestion module Pydantic schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


class ProcessingLogRead(BaseModel):
    """Pipeline step execution log."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    step_name: str
    status: str
    log_message: Optional[str] = None
    duration_ms: int
    timestamp: datetime


class DocumentRead(BaseModel):
    """Full medical document object."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    clinician_id: str
    upload_job_id: Optional[str] = None
    original_filename: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    doc_category: str
    status: str
    parse_source: Optional[str] = None
    confidence_score: float
    extracted_text: Optional[str] = None
    extracted_markdown: Optional[str] = None
    extracted_html: Optional[str] = None
    error_message: Optional[str] = None

    processing_time_ms: int
    document_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentListItem(BaseModel):
    """Lightweight document summary item for workspace table."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size_bytes: int
    doc_category: str
    status: str
    parse_source: Optional[str] = None
    confidence_score: float
    processing_time_ms: int
    document_date: Optional[datetime] = None
    created_at: datetime



class UploadJobRead(BaseModel):
    """Batch upload job status."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    clinician_id: str
    patient_id: str
    total_files: int
    completed_files: int
    failed_files: int
    duplicate_files: int
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None


class TextEntryRequest(BaseModel):
    """Direct copy-pasted clinical text entry."""
    title: str = "Clinical Consultation Note"
    doc_category: str = "note" # note, lab, prescription, vitals, summary
    raw_text: str
    custom_event_date: Optional[str] = None # Optional YYYY-MM-DD override


class BatchUploadSummary(BaseModel):
    """Detailed summary of a completed batch upload."""
    job_id: str
    total_files: int
    completed_files: int
    duplicate_files: int
    failed_files: int
    average_confidence: float
    total_processing_time_ms: int
    documents: List[DocumentRead]


class DocumentProvenanceRead(BaseModel):
    """Full evidence provenance chain for a clinical source document."""

    document_id: str
    patient_id: str
    clinician_id: str

    # File identity
    original_filename: str
    mime_type: str
    file_type: str
    file_size_bytes: int
    sha256_hash: str

    # Clinical context
    doc_category: str
    document_date: Optional[datetime] = None
    uploaded_at: datetime

    # Extraction provenance
    parse_source: Optional[str] = None         # sarvam_parse / sarvam_vision / pymupdf_fallback
    confidence_score: float
    processing_status: str                      # completed / failed / duplicate
    processing_time_ms: int

    # File availability
    file_available: bool
    file_unavailable_reason: Optional[str] = None

    # Evidence chain counts
    timeline_event_count: int = 0
    lab_result_count: int = 0
    parameter_history_count: int = 0
