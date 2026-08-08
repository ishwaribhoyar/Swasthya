"""
Clinical Engine SQLAlchemy Models.

Stores structured lab results, vital signs, 8-organ system health scores, and severity alerts.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class LabResult(Base, TimestampMixin):
    """Structured LOINC-aligned laboratory test result."""

    __tablename__ = "lab_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )

    test_name:     Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    test_code:     Mapped[Optional[str]] = mapped_column(String(50)) # LOINC code or canonical string
    numeric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit:          Mapped[str]   = mapped_column(String(50), nullable=False)
    ref_min:       Mapped[Optional[float]] = mapped_column(Float)
    ref_max:       Mapped[Optional[float]] = mapped_column(Float)
    status:        Mapped[str]   = mapped_column(String(30), nullable=False) # LOW, NORMAL, HIGH, CRITICAL_LOW, CRITICAL_HIGH
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    tested_at:     Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class VitalSign(Base, TimestampMixin):
    """Structured patient vital sign observation."""

    __tablename__ = "vital_signs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )

    sbp:              Mapped[Optional[int]]   = mapped_column(Integer) # Systolic BP mmHg
    dbp:              Mapped[Optional[int]]   = mapped_column(Integer) # Diastolic BP mmHg
    heart_rate:       Mapped[Optional[int]]   = mapped_column(Integer) # Pulse bpm
    spo2:             Mapped[Optional[float]] = mapped_column(Float)   # Oxygen saturation %
    respiratory_rate: Mapped[Optional[int]]   = mapped_column(Integer) # breaths/min
    temperature_c:    Mapped[Optional[float]] = mapped_column(Float)   # Temperature °C
    bmi:              Mapped[Optional[float]] = mapped_column(Float)   # BMI kg/m²
    status:           Mapped[str]             = mapped_column(String(30), default="NORMAL") # NORMAL, ABNORMAL, CRITICAL
    recorded_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OrganScore(Base):
    """Calculated 8-organ system health score (0 - 100%)."""

    __tablename__ = "organ_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    organ_system:           Mapped[str]   = mapped_column(String(50), nullable=False) # hematological, renal, hepatic, cardiovascular, metabolic, respiratory, inflammatory, electrolyte
    score:                  Mapped[Optional[float]] = mapped_column(Float, nullable=True) # 0 to 100 or None if insufficient data

    status:                 Mapped[str]   = mapped_column(String(30), nullable=False) # OPTIMAL, MILD_STRAIN, MODERATE_IMPAIRMENT, SEVERE_DYSFUNCTION
    contributing_biomarkers: Mapped[Optional[str]] = mapped_column(Text) # JSON string of contributing lab/vital names
    rationale:              Mapped[Optional[str]] = mapped_column(Text)
    calculated_at:          Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ClinicalAlert(Base, TimestampMixin):
    """Automated clinical severity alert."""

    __tablename__ = "clinical_alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )

    alert_type:            Mapped[str]  = mapped_column(String(50), nullable=False) # lab_critical, vital_critical, organ_strain
    severity:              Mapped[str]  = mapped_column(String(20), nullable=False) # CRITICAL, HIGH, MODERATE, INFORMATIONAL
    title:                 Mapped[str]  = mapped_column(String(200), nullable=False)
    message:               Mapped[str]  = mapped_column(Text, nullable=False)
    biomarker_name:        Mapped[Optional[str]] = mapped_column(String(100))
    observed_value:        Mapped[Optional[str]] = mapped_column(String(100))
    reference_range:       Mapped[Optional[str]] = mapped_column(String(100))
    action_recommendation: Mapped[Optional[str]] = mapped_column(Text)
    is_acknowledged:       Mapped[bool] = mapped_column(Boolean, default=False)
