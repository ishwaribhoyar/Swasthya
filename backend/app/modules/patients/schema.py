"""
Patient module Pydantic schemas.

All input schemas validate field bounds, formats, and medical constraints.
Output schemas expose structured patient objects and rich clinical statistics.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal, Optional, Dict
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


BloodGroupType = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
GenderType = Literal["male", "female", "other"]


# ─── Input Schemas ────────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    """Body for POST /patients — register a new patient."""

    first_name: str = Field(..., min_length=1, max_length=100, description="Given name")
    last_name:  str = Field(..., min_length=1, max_length=100, description="Family name")
    date_of_birth: date = Field(..., description="Format: YYYY-MM-DD")
    gender: GenderType
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    blood_group: Optional[BloodGroupType] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = Field(None, max_length=500)
    allergies: Optional[str] = Field(None, max_length=1000)
    chronic_conditions: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        """Ensure Date of Birth is not in the future."""
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


class PatientUpdate(BaseModel):
    """Body for PATCH /patients/{id} — partial update."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name:  Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderType] = None
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    blood_group: Optional[BloodGroupType] = None
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=30)
    address: Optional[str] = Field(None, max_length=500)
    allergies: Optional[str] = Field(None, max_length=1000)
    chronic_conditions: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


# ─── Output Schemas ───────────────────────────────────────────────────────────

class PatientRead(BaseModel):
    """Full patient record object."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    clinician_id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    gender: str
    phone: Optional[str] = None
    email: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PatientListItem(BaseModel):
    """Lightweight patient summary item for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    gender: str
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    is_active: bool
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_document_at: Optional[datetime] = None
    risk_status: Optional[str] = None  # NORMAL | HIGH | CRITICAL | None


class PatientStatisticsResponse(BaseModel):
    """Rich patient metrics and distributions for clinician dashboard."""

    total_patients: int
    active_patients: int
    archived_patients: int
    new_this_month: int
    gender_distribution: Dict[str, int]
    blood_group_distribution: Dict[str, int]
    age_distribution: Dict[str, int]
