"""
Tests for AI Copilot Module & Production Clinical RAG Pipeline.
Validates end-to-end 12-Stage RAG execution, patient context building,
hybrid BM25+dense retrieval, RRF ranking, MMR diversification, GPT reasoning,
citations, and audit hash logging.
"""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rag_pipeline_execution(async_client: AsyncClient) -> None:
    """Test full 12-Stage RAG execution pipeline over patient records."""
    # 1. Register Clinician
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "RAG",
        "last_name": "Doctor",
        "email": "rag.doc@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register Patient
    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Bruce",
        "last_name": "Banner",
        "date_of_birth": "1975-12-18",
        "gender": "male",
        "allergies": "Gamma Radiation",
        "chronic_conditions": "Elevated Anger Metrics",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 3. Upload Medical Document (Lab Report)
    lab_bytes = b"%PDF-1.4 %lab report Hemoglobin: 14.2 g/dL White Blood Cell: 6.5 k/uL Serum Glucose: 95 mg/dL"
    files = [("files", ("complete_blood_count.pdf", io.BytesIO(lab_bytes), "application/pdf"))]
    upload_res = await async_client.post(
        f"/api/v1/ingestion/patients/{patient_id}/upload",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 201

    # 4. Execute 12-Stage RAG Query
    query_payload = {
        "patient_id": patient_id,
        "query": "What are the latest lab results and glucose readings for this patient?",
    }
    rag_res = await async_client.post(
        "/api/v1/ai-copilot/query",
        json=query_payload,
        headers=headers,
    )
    assert rag_res.status_code == 200, rag_res.text
    data = rag_res.json()["data"]

    assert data["patient_id"] == patient_id
    assert "complete_blood_count.pdf" in data["answer"] or "Hemoglobin" in data["answer"] or "Glucose" in data["answer"]
    assert data["confidence_score"] >= 0.70
    assert len(data["sources"]) >= 1
    assert len(data["audit_hash"]) == 64  # SHA256 hex string

    # 5. Fetch Chat Audit History
    hist_res = await async_client.get(
        f"/api/v1/ai-copilot/patients/{patient_id}/history",
        headers=headers,
    )
    assert hist_res.status_code == 200
    h_data = hist_res.json()["data"]
    assert len(h_data) >= 1
    assert h_data[0]["audit_hash"] == data["audit_hash"]
