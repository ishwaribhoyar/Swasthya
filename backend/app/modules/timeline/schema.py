"""
Pydantic schemas for Timeline Intelligence Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class TimelineEventRead(BaseModel):
    """Structured clinical timeline event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    record_id: Optional[str] = None
    event_date: datetime
    date_priority_source: str
    event_type: str
    document_type: str
    title: str
    summary: str
    confidence: float
    entities_json: str
    created_at: datetime


class VisitGroupRead(BaseModel):
    """Multiple clinical events grouped under the same visit date."""

    visit_date: str
    display_date: str
    event_count: int
    categories: List[str]
    events: List[TimelineEventRead]
