"""
Longitudinal Trend Analytics & Anomaly Detection Engine.

Analyzes historical parameter measurements from parameter_history table to compute:
  - Time-series observation points (date, value, unit, status, source_record_id)
  - Longitudinal Shift (absolute change, percentage change)
  - Rate of Change per Day & Time Span in days
  - Direction: STABLE, INCREASING, DECREASING, RAPIDLY_INCREASING, RAPIDLY_DECREASING, OSCILLATING
  - Clinical Anomalies: Panic Values, Sudden Changes, Repeated High Values
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Sequence
from app.modules.analytics.model import ParameterHistory
from app.observability.logger import get_logger

_log = get_logger(__name__)


class TrendResult:
    """Longitudinal trend analysis result per parameter matching frontend IParameterTrend interface."""

    def __init__(
        self,
        parameter_name: str,
        normalized_name: str,
        unit: str,
        latest_value: float,
        latest_date: str,
        direction: str,
        absolute_change: float,
        percentage_change: float,
        rate_of_change_per_day: float,
        observation_count: int,
        time_span_days: int,
        confidence: float,
        anomalies: List[str],
        points: List[Dict],
    ) -> None:
        self.parameter_name = parameter_name
        self.normalized_name = normalized_name
        self.unit = unit
        self.latest_value = latest_value
        self.latest_date = latest_date
        self.direction = direction
        self.absolute_change = absolute_change
        self.percentage_change = percentage_change
        self.rate_of_change_per_day = rate_of_change_per_day
        self.observation_count = observation_count
        self.time_span_days = time_span_days
        self.confidence = confidence
        self.anomalies = anomalies
        self.points = points

    def to_dict(self) -> Dict:
        return {
            "parameter_name": self.parameter_name,
            "normalized_name": self.normalized_name,
            "unit": self.unit,
            "latest_value": self.latest_value,
            "latest_date": self.latest_date,
            "direction": self.direction,
            "absolute_change": self.absolute_change,
            "percentage_change": self.percentage_change,
            "rate_of_change_per_day": self.rate_of_change_per_day,
            "observation_count": self.observation_count,
            "time_span_days": self.time_span_days,
            "confidence": self.confidence,
            "anomalies": self.anomalies,
            "points": self.points,
        }


class TrendEngine:
    """Longitudinal Trend & Anomaly Detection Engine."""

    @classmethod
    def analyze_parameter_series(
        cls, parameter_name: str, items: Sequence[ParameterHistory]
    ) -> TrendResult:
        """
        Compute longitudinal trend metrics and anomaly detections for a parameter time-series.
        """
        if not items:
            return TrendResult(
                parameter_name=parameter_name,
                normalized_name=parameter_name.lower().replace(" ", "_"),
                unit="",
                latest_value=0.0,
                latest_date="",
                direction="STABLE",
                absolute_change=0.0,
                percentage_change=0.0,
                rate_of_change_per_day=0.0,
                observation_count=0,
                time_span_days=0,
                confidence=1.0,
                anomalies=[],
                points=[],
            )

        # Sort chronologically by event_date
        sorted_items = sorted(items, key=lambda x: x.event_date)
        obs_count = len(sorted_items)

        points = [
            {
                "date": item.event_date.strftime("%Y-%m-%d") if item.event_date else "",
                "value": item.value,
                "unit": item.unit,
                "status": item.status,
                "source_record_id": item.record_id,
            }
            for item in sorted_items
        ]

        unit = sorted_items[0].unit or ""
        norm_name = sorted_items[0].normalized_name or parameter_name.lower().replace(" ", "_")

        latest_item = sorted_items[-1]
        latest_val = latest_item.value
        latest_dt_str = latest_item.event_date.strftime("%Y-%m-%d") if latest_item.event_date else ""

        first_item = sorted_items[0]
        first_val = first_item.value

        if obs_count <= 1:
            return TrendResult(
                parameter_name=parameter_name,
                normalized_name=norm_name,
                unit=unit,
                latest_value=latest_val,
                latest_date=latest_dt_str,
                direction="STABLE",
                absolute_change=0.0,
                percentage_change=0.0,
                rate_of_change_per_day=0.0,
                observation_count=1,
                time_span_days=0,
                confidence=0.85,
                anomalies=[] if latest_item.status == "NORMAL" else [f"Single baseline {latest_item.status.lower()} value"],
                points=points,
            )

        # Calculate time span, absolute shift & percentage change
        days_span = max(1, (latest_item.event_date - first_item.event_date).days)
        abs_change = round(latest_val - first_val, 2)
        pct_change = round((abs_change / max(0.001, abs(first_val))) * 100.0, 1)
        rate_per_day = round(abs_change / float(days_span), 3)

        # Determine Direction
        if abs(pct_change) < 3.0:
            direction = "STABLE"
        elif pct_change >= 25.0:
            direction = "RAPIDLY_INCREASING"
        elif pct_change > 0:
            direction = "INCREASING"
        elif pct_change <= -25.0:
            direction = "RAPIDLY_DECREASING"
        else:
            direction = "DECREASING"

        # Check for Oscillating trend
        if obs_count >= 3:
            diffs = [sorted_items[i + 1].value - sorted_items[i].value for i in range(obs_count - 1)]
            sign_changes = sum(1 for i in range(len(diffs) - 1) if (diffs[i] * diffs[i + 1]) < 0)
            if sign_changes >= 2:
                direction = "OSCILLATING"

        # Anomaly Detection
        anomalies: List[str] = []
        has_critical = any(item.status == "CRITICAL" for item in sorted_items)
        repeated_high = sum(1 for item in sorted_items if item.status in ("HIGH", "CRITICAL"))

        if has_critical:
            anomalies.append(f"Panic Value Triggered: {latest_val} {unit}")
        if repeated_high >= 2:
            anomalies.append(f"Repeated Elevated Measurements ({repeated_high} instances)")
        if abs(pct_change) >= 40.0:
            anomalies.append(f"Sudden Shift Detected ({pct_change:+.1f}%)")

        confidence = 1.0 if obs_count >= 3 else 0.90

        return TrendResult(
            parameter_name=parameter_name,
            normalized_name=norm_name,
            unit=unit,
            latest_value=latest_val,
            latest_date=latest_dt_str,
            direction=direction,
            absolute_change=abs_change,
            percentage_change=pct_change,
            rate_of_change_per_day=rate_per_day,
            observation_count=obs_count,
            time_span_days=days_span,
            confidence=confidence,
            anomalies=anomalies,
            points=points,
        )
