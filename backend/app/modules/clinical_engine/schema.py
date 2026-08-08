"""
Clinical Engine Pydantic Schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class LabResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    document_id: Optional[str] = None
    test_name: str
    test_code: Optional[str] = None
    numeric_value: float
    unit: str
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    status: str
    confidence_score: float
    tested_at: datetime


class VitalSignRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    document_id: Optional[str] = None
    sbp: Optional[int] = None
    dbp: Optional[int] = None
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    respiratory_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    bmi: Optional[float] = None
    status: str
    recorded_at: datetime


class OrganScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    organ_system: str
    score: Optional[float] = None

    status: str
    contributing_biomarkers: Optional[str] = None
    rationale: Optional[str] = None
    calculated_at: datetime


class ClinicalAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    document_id: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    message: str
    biomarker_name: Optional[str] = None
    observed_value: Optional[str] = None
    reference_range: Optional[str] = None
    action_recommendation: Optional[str] = None
    is_acknowledged: bool
    created_at: datetime


class ClinicalOverviewRead(BaseModel):
    patient_id: str
    organ_scores: List[OrganScoreRead]
    alerts: List[ClinicalAlertRead]
    latest_labs: List[LabResultRead]
    latest_vitals: Optional[VitalSignRead] = None
    analyzed_documents_count: int
