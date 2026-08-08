"""
Medicine Engine Pydantic Schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class PrescriptionMedicineRead(BaseModel):
    """Pydantic schema for an individual medicine within a prescription."""

    id: str
    prescription_id: str
    patient_id: str
    clinician_id: str
    medicine_name: str
    strength: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PrescriptionRead(BaseModel):
    """Pydantic schema for a prescription header with medicines."""

    id: str
    patient_id: str
    clinician_id: str
    document_id: Optional[str] = None
    prescribed_by: Optional[str] = None
    prescription_date: datetime
    notes: Optional[str] = None
    medicines: List[PrescriptionMedicineRead] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicineSummaryRead(BaseModel):
    """Pydantic schema for aggregated patient medicine summary item."""

    medicine_name: str
    times_prescribed: int
    first_prescribed_date: datetime
    latest_prescribed_date: datetime
    latest_strength: Optional[str] = None
    latest_dose: Optional[str] = None
    latest_frequency: Optional[str] = None
    latest_route: Optional[str] = None
    status: str = "ACTIVE" # ACTIVE, DISCONTINUED


class MedicineHistoryRead(BaseModel):
    """Pydantic schema for detailed history of a single medicine."""

    medicine_name: str
    total_prescriptions: int
    first_prescribed: datetime
    latest_prescribed: datetime
    prescription_events: List[PrescriptionMedicineRead] = []
