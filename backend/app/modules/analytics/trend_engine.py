"""
Longitudinal Trend Analytics & Anomaly Detection Engine.

Analyzes historical parameter measurements from parameter_history table to detect:
  - Longitudinal Trends: Stable, Increasing, Rapid Increase, Decreasing, Rapid Decrease, Oscillating, Critical Rise
  - Clinical Anomalies: Panic Values, Sudden Changes, Repeated High BP, Repeated High Glucose, Repeated High Creatinine
  - Chart-Ready JSON structures for Recharts visualization.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Sequence
from app.modules.analytics.model import ParameterHistory
from app.observability.logger import get_logger

_log = get_logger(__name__)


class TrendResult:
    """Longitudinal trend analysis result per parameter."""

    def __init__(
        self,
        parameter_name: str,
        normalized_name: str,
        unit: str,
        direction: str,
        rate_of_change: str,
        risk_level: str,
        anomaly: Optional[str],
        data_points: List[Dict],
    ) -> None:
        self.parameter_name = parameter_name
        self.normalized_name = normalized_name
        self.unit = unit
        self.direction = direction
        self.rate_of_change = rate_of_change
        self.risk_level = risk_level
        self.anomaly = anomaly
        self.data_points = data_points

    def to_dict(self) -> Dict:
        return {
            "parameter_name": self.parameter_name,
            "normalized_name": self.normalized_name,
            "unit": self.unit,
            "direction": self.direction,
            "rate_of_change": self.rate_of_change,
            "risk_level": self.risk_level,
            "anomaly": self.anomaly,
            "data_points": self.data_points,
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
        # Sort chronologically by event_date
        sorted_items = sorted(items, key=lambda x: x.event_date)

        data_points = [
            {
                "date": item.event_date.strftime("%Y-%m-%d") if item.event_date else "",
                "timestamp": item.event_date.isoformat() if item.event_date else "",
                "value": item.value,
                "value_str": item.value_str,
                "unit": item.unit,
                "status": item.status,
                "reference_range": item.reference_range,
            }
            for item in sorted_items
        ]

        unit = sorted_items[0].unit if sorted_items else ""
        norm_name = sorted_items[0].normalized_name if sorted_items else parameter_name.lower().replace(" ", "_")

        if len(sorted_items) <= 1:
            val = sorted_items[0].value if sorted_items else 0.0
            status = sorted_items[0].status if sorted_items else "NORMAL"
            return TrendResult(
                parameter_name=parameter_name,
                normalized_name=norm_name,
                unit=unit,
                direction="Stable",
                rate_of_change="0.0%",
                risk_level=status,
                anomaly=None if status == "NORMAL" else f"Single Baseline {status} Value",
                data_points=data_points,
            )

        # Calculate slope & percentage change
        first_val = sorted_items[0].value
        last_val = sorted_items[-1].value
        diff = last_val - first_val
        pct_change = (diff / max(0.001, abs(first_val))) * 100.0

        # Determine Direction & Rate of Change
        if abs(pct_change) < 3.0:
            direction = "Stable"
            rate = "Stable (±3%)"
        elif pct_change >= 25.0:
            direction = "Rapid Increase"
            rate = f"+{pct_change:.1f}%"
        elif pct_change > 0:
            direction = "Increasing"
            rate = f"+{pct_change:.1f}%"
        elif pct_change <= -25.0:
            direction = "Rapid Decrease"
            rate = f"{pct_change:.1f}%"
        else:
            direction = "Decreasing"
            rate = f"{pct_change:.1f}%"

        # Check for Oscillating trend
        if len(sorted_items) >= 3:
            diffs = [sorted_items[i+1].value - sorted_items[i].value for i in range(len(sorted_items)-1)]
            sign_changes = sum(1 for i in range(len(diffs)-1) if (diffs[i] * diffs[i+1]) < 0)
            if sign_changes >= 2:
                direction = "Oscillating"

        # Anomaly Detection
        anomaly = None
        has_critical = any(item.status == "CRITICAL" for item in sorted_items)
        repeated_high = sum(1 for item in sorted_items if item.status in ("HIGH", "CRITICAL"))

        if has_critical:
            direction = "Critical Rise" if pct_change > 0 else "Critical Fall"
            anomaly = f"Panic Value Triggered: {last_val} {unit}"
            risk_level = "CRITICAL"
        elif repeated_high >= 2:
            anomaly = f"Repeated High Values ({repeated_high} instances)"
            risk_level = "HIGH"
        elif abs(pct_change) >= 40.0:
            anomaly = f"Sudden Change Detected ({pct_change:+.1f}%)"
            risk_level = "HIGH"
        else:
            risk_level = sorted_items[-1].status

        return TrendResult(
            parameter_name=parameter_name,
            normalized_name=norm_name,
            unit=unit,
            direction=direction,
            rate_of_change=rate,
            risk_level=risk_level,
            anomaly=anomaly,
            data_points=data_points,
        )
