"""
Pydantic schemas for Trend Analytics & Risk Detection Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ParameterDataPoint(BaseModel):
    """Single measurement point in time-series."""

    date: str
    timestamp: str
    value: float
    value_str: str
    unit: str
    status: str
    reference_range: str


class ParameterTrendRead(BaseModel):
    """Longitudinal trend & anomaly analysis result for a single parameter."""

    parameter_name: str
    normalized_name: str
    unit: str
    direction: str # Stable, Increasing, Rapid Increase, Decreasing, Rapid Decrease, Oscillating, Critical Rise
    rate_of_change: str
    risk_level: str # NORMAL, HIGH, LOW, CRITICAL
    anomaly: Optional[str] = None
    data_points: List[ParameterDataPoint]


class AnalyticsOverviewRead(BaseModel):
    """Full patient analytics overview containing all tracked parameter trends & anomalies."""

    patient_id: str
    total_parameters_tracked: int
    critical_anomalies_count: int
    parameter_trends: List[ParameterTrendRead]
