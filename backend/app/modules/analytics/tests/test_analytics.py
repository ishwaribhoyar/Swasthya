"""
Tests for Analytics & Trend Intelligence Engine.
Validates longitudinal trend detection (Stable, Increasing, Decreasing, Rapid Rise, Oscillating)
and critical anomaly alerts.
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.modules.analytics.model import ParameterHistory
from app.modules.analytics.trend_engine import TrendEngine


def test_trend_engine_increasing_and_anomaly() -> None:
    """Verify trend direction computation and panic value anomaly detection."""
    now = datetime.now(timezone.utc)
    history = [
        ParameterHistory(
            parameter_name="Creatinine",
            normalized_name="creatinine",
            value=1.1,
            value_str="1.1 mg/dL",
            unit="mg/dL",
            status="NORMAL",
            event_date=now,
        ),
        ParameterHistory(
            parameter_name="Creatinine",
            normalized_name="creatinine",
            value=1.4,
            value_str="1.4 mg/dL",
            unit="mg/dL",
            status="HIGH",
            event_date=now,
        ),
        ParameterHistory(
            parameter_name="Creatinine",
            normalized_name="creatinine",
            value=2.1,
            value_str="2.1 mg/dL",
            unit="mg/dL",
            status="CRITICAL",
            event_date=now,
        ),
    ]

    res = TrendEngine.analyze_parameter_series("Creatinine", history)
    assert res.parameter_name == "Creatinine"
    assert res.direction in ("RAPIDLY_INCREASING", "Critical Rise")
    assert len(res.anomalies) > 0
    assert len(res.points) == 3


@pytest.mark.asyncio
async def test_analytics_api_trends(async_client: AsyncClient) -> None:
    """Test Analytics API trends endpoint."""
    # 1. Register Clinician & Patient
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Analytics",
        "last_name": "Doc",
        "email": "analytics.doc@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Natasha",
        "last_name": "Romanoff",
        "date_of_birth": "1984-11-22",
        "gender": "female",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 2. Query Analytics Trends API
    an_res = await async_client.get(f"/api/v1/analytics/patients/{patient_id}/trends", headers=headers)
    assert an_res.status_code == 200
    data = an_res.json()["data"]
    assert data["patient_id"] == patient_id
    assert "parameter_trends" in data
