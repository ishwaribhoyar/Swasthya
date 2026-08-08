"""
Pydantic schemas for Trend Analytics & Risk Detection Engine.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ParameterDataPoint(BaseModel):
    """Single measurement point in time-series."""

    date: str
    value: float
    unit: str
    status: str
    source_record_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ParameterTrendRead(BaseModel):
    """Longitudinal trend & anomaly analysis result matching frontend IParameterTrend."""

    parameter_name: str
    normalized_name: str
    unit: str
    latest_value: float
    latest_date: str
    direction: str  # STABLE, INCREASING, DECREASING, RAPIDLY_INCREASING, RAPIDLY_DECREASING, OSCILLATING
    absolute_change: float
    percentage_change: float
    rate_of_change_per_day: float
    observation_count: int
    time_span_days: int
    confidence: float
    anomalies: List[str] = []
    points: List[ParameterDataPoint] = []

    model_config = ConfigDict(from_attributes=True)


class AnalyticsOverviewRead(BaseModel):
    """Full patient analytics overview containing all tracked parameter trends & anomalies."""

    patient_id: str
    total_parameters_tracked: int
    critical_anomalies_count: int
    active_anomalies: List[str] = []
    parameter_trends: List[ParameterTrendRead]

    model_config = ConfigDict(from_attributes=True)
