"""
Patient SQLAlchemy model.

Represents a clinical patient registered by a clinician.
All patient data originates from clinician input — no records
are pre-populated or seeded. Every patient belongs to exactly ONE clinician.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, String, Text, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Patient(Base, TimestampMixin):
    """
    Clinical patient record.

    Attributes:
        id:                      UUID primary key.
        clinician_id:            User.id of the clinician who owns this patient.
        mrn:                     Medical Record Number (sequential format MRN-YYYY-######).
        first_name:              Patient's given name.
        last_name:               Patient's family name.
        date_of_birth:           ISO date. Used to calculate age.
        gender:                  Biological sex / gender identity (male, female, other).
        phone:                   Contact phone number.
        email:                   Contact email (optional).
        address:                 Free-text address (optional).
        blood_group:             ABO + Rh blood group (A+, A-, B+, B-, AB+, AB-, O+, O-).
        emergency_contact_name:  Name of emergency contact person.
        emergency_contact_phone: Phone number of emergency contact person.
        allergies:               Free-text list of known allergies.
        chronic_conditions:      Known pre-existing chronic medical conditions.
        notes:                   General clinical notes.
        is_active:               True for active patients, False for archived patients.
        archived_at:             Timestamp when patient was archived (soft deleted).
        created_by:              User.id of creator (same as clinician_id).
    """

    __tablename__ = "patients"
    __allow_unmapped__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    clinician_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    mrn: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name:  Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(
        SAEnum("male", "female", "other", name="patient_gender"),
        nullable=False,
    )
    phone:                   Mapped[Optional[str]] = mapped_column(String(30))
    email:                   Mapped[Optional[str]] = mapped_column(String(255))
    address:                 Mapped[Optional[str]] = mapped_column(Text)
    blood_group:             Mapped[Optional[str]] = mapped_column(String(10))
    emergency_contact_name:  Mapped[Optional[str]] = mapped_column(String(100))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(30))
    allergies:               Mapped[Optional[str]] = mapped_column(Text)
    chronic_conditions:      Mapped[Optional[str]] = mapped_column(Text)
    notes:                   Mapped[Optional[str]] = mapped_column(Text)
    is_active:               Mapped[bool]          = mapped_column(Boolean, default=True, nullable=False, index=True)
    archived_at:             Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by:              Mapped[str]           = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    __table_args__ = (
        Index("ix_patients_clinician_active", "clinician_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} mrn={self.mrn} name={self.first_name} {self.last_name}>"

    # Dynamically set by PatientRepository.list_patients — not DB columns
    last_document_at: Optional[datetime] = None
    risk_status: Optional[str] = None
