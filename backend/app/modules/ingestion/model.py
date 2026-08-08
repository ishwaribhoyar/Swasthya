"""
Ingestion module SQLAlchemy models.

Stores upload jobs, document metadata, processing status, and step-by-step audit logs.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UploadJob(Base, TimestampMixin):
    """
    Batch upload job tracking up to 10 documents processed concurrently or sequentially.
    """

    __tablename__ = "upload_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_files:     Mapped[int] = mapped_column(Integer, nullable=False)
    completed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files:    Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status:          Mapped[str] = mapped_column(String(20), default="processing", nullable=False)
    finished_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Document(Base, TimestampMixin):
    """
    Uploaded medical document metadata and extracted content.
    """

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("upload_jobs.id", ondelete="SET NULL"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type:         Mapped[str] = mapped_column(String(20), nullable=False) # pdf, image
    mime_type:         Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes:   Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash:       Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path:      Mapped[str] = mapped_column(Text, nullable=False)
    doc_category:      Mapped[str] = mapped_column(String(50), default="unclassified", nullable=False, index=True) # lab, prescription, vitals, note, summary
    status:            Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True) # queued, uploading, processing, completed, failed, duplicate, cancelled
    parse_source:      Mapped[Optional[str]] = mapped_column(String(50)) # sarvam_parse, sarvam_vision, pymupdf_fallback
    confidence_score:  Mapped[float]         = mapped_column(Float, default=1.0)
    extracted_text:    Mapped[Optional[str]] = mapped_column(Text)
    extracted_markdown: Mapped[Optional[str]] = mapped_column(Text)
    extracted_html:    Mapped[Optional[str]] = mapped_column(Text)
    error_message:     Mapped[Optional[str]] = mapped_column(Text)

    processing_time_ms: Mapped[int]          = mapped_column(Integer, default=0)
    document_date:      Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (

        Index("ix_documents_patient_sha256", "patient_id", "sha256_hash"),
    )


class ProcessingLog(Base):
    """
    Step-by-step pipeline execution logs for visual processing timeline.
    """

    __tablename__ = "processing_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_name:   Mapped[str] = mapped_column(String(50), nullable=False) # upload, sha256_check, router, parsing, normalization, persistence
    status:      Mapped[str] = mapped_column(String(20), nullable=False) # started, completed, failed, skipped
    log_message: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    timestamp:   Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
