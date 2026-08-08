"""
SQLAlchemy ORM model for longitudinal parameter history tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class ParameterHistory(Base, TimestampMixin):
    """Longitudinal clinical parameter record (Labs, Vitals, Biometrics)."""

    __tablename__ = "parameter_history"

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

    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. "HbA1c", "Glucose", "Systolic BP"
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True) # e.g. "hba1c", "glucose", "systolic_bp"
    value: Mapped[float] = mapped_column(Float, nullable=False)
    value_str: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    reference_range: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="NORMAL", nullable=False, index=True) # NORMAL, HIGH, LOW, CRITICAL
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.98, nullable=False)

    __table_args__ = (
        Index("ix_parameter_history_patient_param_date", "patient_id", "normalized_name", "event_date"),
    )
