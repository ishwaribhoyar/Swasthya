"""
Tests for Timeline Intelligence Engine.
Validates 10-level priority event date extraction, medicine normalization,
and visit grouping.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.modules.timeline.event_extractor import PriorityEventExtractor


def test_priority_date_extraction() -> None:
    """Verify priority hierarchy for event date extraction."""
    text = (
        "Sample Collection Date: 2026-08-01\n"
        "Visit Date: 2026-08-03\n"
        "Report Date: 2026-08-05\n"
        "Lab Results: Hemoglobin: 14.5 g/dL, Glucose: 98 mg/dL\n"
        "Prescribed: Paracetamol 500mg"
    )
    ev = PriorityEventExtractor.extract_priority_event(
        filename="blood_report.pdf", category="lab", text=text
    )

    # Sample Collection Date (2026-08-01) takes priority over Visit and Report dates
    assert ev.event_date.strftime("%Y-%m-%d") == "2026-08-01"
    assert ev.date_priority_source == "sample_collection"
    assert len(ev.parameters) >= 2
    assert ev.entities["medicines"][0]["name"] == "Paracetamol 500mg"


@pytest.mark.asyncio
async def test_timeline_api_and_visit_grouping(async_client: AsyncClient) -> None:
    """Test full document upload and API timeline retrieval grouped by visit date."""
    # 1. Register Clinician & Patient
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Timeline",
        "last_name": "Doc",
        "email": "timeline.doc@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Steve",
        "last_name": "Rogers",
        "date_of_birth": "1920-07-04",
        "gender": "male",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 2. Upload Lab Document
    lab_bytes = b"%PDF-1.4 Sample Collection Date: 2026-08-02\nHemoglobin: 13.8 g/dL Glucose: 92 mg/dL"
    files = [("files", ("cbc_panel.pdf", io.BytesIO(lab_bytes), "application/pdf"))]
    await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/upload", files=files, headers=headers)

    # 3. Query Timeline API
    t_res = await async_client.get(f"/api/v1/timeline/patients/{patient_id}", headers=headers)
    assert t_res.status_code == 200
    groups = t_res.json()["data"]
    assert len(groups) >= 1
    assert groups[0]["visit_date"] == "2026-08-02"
    assert len(groups[0]["events"]) >= 1
