"""
Prescription and PrescriptionMedicine SQLAlchemy Models.

Stores structured medication histories extracted from prescriptions or clinical notes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Prescription(Base, TimestampMixin):
    """Structured Prescription Header Record."""

    __tablename__ = "prescriptions"

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

    prescribed_by: Mapped[Optional[str]] = mapped_column(String(150))
    prescription_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text)

    medicines: Mapped[List[PrescriptionMedicine]] = relationship(
        "PrescriptionMedicine", back_populates="prescription", cascade="all, delete-orphan"
    )


class PrescriptionMedicine(Base, TimestampMixin):
    """Individual Medication Item within a Prescription."""

    __tablename__ = "prescription_medicines"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    prescription_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    medicine_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    strength: Mapped[Optional[str]] = mapped_column(String(50)) # e.g. 500mg, 10mg/ml
    dose: Mapped[Optional[str]] = mapped_column(String(50))     # e.g. 1 tablet, 5ml
    frequency: Mapped[Optional[str]] = mapped_column(String(50))# e.g. Once daily, BID, TID, PRN
    route: Mapped[Optional[str]] = mapped_column(String(50))    # e.g. Oral, IV, Topical
    duration_days: Mapped[Optional[int]] = mapped_column(Integer) # e.g. 7, 30
    instructions: Mapped[Optional[str]] = mapped_column(Text)  # e.g. After meals

    prescription: Mapped[Prescription] = relationship("Prescription", back_populates="medicines")
