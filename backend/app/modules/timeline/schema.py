"""
Pydantic schemas for the Clinical Timeline Intelligence Engine.

Schema hierarchy:
  ClinicalObservation   — one extracted parameter/measurement
  ClinicalEncounterRead — one encounter (document) with all its observations
  VisitGroupRead        — all encounters grouped under one calendar date
  TimelineStatsRead     — longitudinal statistics for the timeline header
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClinicalObservation(BaseModel):
    """A single extracted clinical measurement."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    value: Optional[float] = None
    value_str: str
    unit: str
    status: str  # NORMAL, HIGH, LOW, CRITICAL_HIGH, CRITICAL_LOW, UNKNOWN
    reference_range: Optional[str] = None
    category: str  # lab, vitals, medicine


class ClinicalEncounterRead(BaseModel):
    """A single clinical encounter reconstructed from a medical document."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    event_date: datetime
    display_date: str
    event_type: str
    document_type: str
    title: str
    summary: Optional[str] = None
    processing_incomplete: bool = False
    processing_reason: Optional[str] = None
    date_priority_source: str
    confidence: float
    observations: List[ClinicalObservation] = []
    record_id: Optional[str] = None


class VisitGroupRead(BaseModel):
    """All clinical encounters grouped under one calendar date."""

    visit_date: str
    display_date: str
    day_label: str
    event_count: int
    observation_count: int
    incomplete_count: int
    categories: List[str]
    encounters: List[ClinicalEncounterRead]


class TimelineStatsRead(BaseModel):
    """Longitudinal statistics for the clinical timeline header card."""

    total_events: int
    first_record: Optional[str] = None
    latest_record: Optional[str] = None
    lab_count: int
    vitals_count: int
    prescription_count: int
    note_count: int


# Legacy aliases kept for router compatibility
TimelineEventRead = ClinicalEncounterRead
