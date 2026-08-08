"""
SQLAlchemy ORM model for canonical longitudinal timeline events.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class TimelineEvent(Base, TimestampMixin):
    """Canonical clinical timeline event reconstructed from medical records."""

    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    record_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )

    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    date_priority_source: Mapped[str] = mapped_column(String(50), default="sample_collection", nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # visit, lab_report, prescription, vitals, note, summary
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.98, nullable=False)
    entities_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    __table_args__ = (
        Index("ix_timeline_events_patient_date", "patient_id", "event_date"),
    )
