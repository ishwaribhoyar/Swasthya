"""
Unit and Integration Tests for Clinical Intelligence Engine.
Validates MedicalParser, OrganScoringEngine, AlertEngine, and Clinical API endpoints.
"""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient

from app.modules.clinical_engine.alert_engine import AlertEngine
from app.modules.clinical_engine.medical_parser import MedicalParser
from app.modules.clinical_engine.organ_scoring import OrganScoringEngine


def test_medical_parser_labs_and_vitals() -> None:
    """Test deterministic lab and vitals extraction."""
    sample_text = """
    LABORATORY REPORT
    Hemoglobin: 14.2 g/dL
    White Blood Cell: 6.5 k/uL
    Platelets: 250 k/uL
    Serum Glucose: 110 mg/dL
    Serum Creatinine: 1.8 mg/dL
    Serum Potassium: 6.2 mEq/L
    SpO2: 88%
    BP: 185/95
    Pulse: 98
    """
    labs = MedicalParser.parse_labs(sample_text)
    assert len(labs) >= 5

    names = [l["test_name"] for l in labs]
    assert "Hemoglobin" in names
    assert "Serum Creatinine" in names
    assert "Serum Potassium" in names

    # Potassium > 6.0 should be CRITICAL_HIGH
    k_lab = next(l for l in labs if l["test_name"] == "Serum Potassium")
    assert k_lab["status"] == "CRITICAL_HIGH"

    vitals = MedicalParser.parse_vitals(sample_text)
    assert vitals["sbp"] == 185
    assert vitals["dbp"] == 95
    assert vitals["spo2"] == 88.0
    assert vitals["status"] == "CRITICAL"


def test_organ_scoring_and_alert_engine() -> None:
    """Test 8-organ health scores and critical alert generation."""
    labs = [
        {"test_name": "Hemoglobin", "numeric_value": 14.2, "unit": "g/dL", "ref_min": 12.0, "ref_max": 17.5, "status": "NORMAL"},
        {"test_name": "Serum Creatinine", "numeric_value": 2.5, "unit": "mg/dL", "ref_min": 0.6, "ref_max": 1.2, "status": "HIGH"},
        {"test_name": "Serum Potassium", "numeric_value": 6.3, "unit": "mEq/L", "ref_min": 3.5, "ref_max": 5.0, "status": "CRITICAL_HIGH"},
    ]
    vitals = {"sbp": 190, "dbp": 100, "spo2": 88.0, "heart_rate": 105, "status": "CRITICAL"}

    scores = OrganScoringEngine.calculate_scores(labs, vitals)
    assert len(scores) == 8

    # Cardiovascular should show strain due to SBP 190
    card = next(s for s in scores if s["organ_system"] == "cardiovascular")
    assert card["score"] < 70

    alerts = AlertEngine.generate_alerts(labs, vitals)
    assert len(alerts) >= 3

    severities = [a["severity"] for a in alerts]
    assert "CRITICAL" in severities


@pytest.mark.asyncio
async def test_clinical_engine_full_pipeline_api(async_client: AsyncClient) -> None:
    """End-to-End Test: Register Clinician -> Register Patient -> Ingest Lab Document -> Trigger Analysis -> Fetch Overview."""
    # 1. Auth
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "House",
        "last_name": "MD",
        "email": "dr.house@diagnostics.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Patient
    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Gregory",
        "last_name": "House",
        "date_of_birth": "1975-05-15",
        "gender": "male",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 3. Ingest Lab Document
    report_content = b"LABORATORY REPORT\nHemoglobin: 14.5 g/dL\nSerum Glucose: 140 mg/dL\nSerum Creatinine: 0.9 mg/dL\nSpO2: 97%\nBP: 120/80"
    files = [("files", ("lab_panel.txt", io.BytesIO(report_content), "text/plain"))]
    await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/upload", files=files, headers=headers)

    # 4. Trigger Analysis
    ana_res = await async_client.post(f"/api/v1/clinical/patients/{patient_id}/analyze", headers=headers)
    assert ana_res.status_code == 200, ana_res.text
    data = ana_res.json()["data"]
    assert data["patient_id"] == patient_id
    assert len(data["organ_scores"]) == 8
    assert len(data["latest_labs"]) >= 3

    # 5. Fetch Organ Scores
    scores_res = await async_client.get(f"/api/v1/clinical/patients/{patient_id}/organ-scores", headers=headers)
    assert scores_res.status_code == 200
    assert len(scores_res.json()["data"]) == 8
