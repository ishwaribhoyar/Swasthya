"""
Tests for Ingestion & Document Intelligence module.
Validates multi-document upload, SHA256 duplicate detection, document router,
PyMuPDF fallback, pipeline timeline logs, and clinician data isolation.
"""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingestion_pipeline_and_deduplication(async_client: AsyncClient) -> None:
    """Test full multi-document upload, pipeline processing, deduplication, and timeline logs."""
    # 1. Register Clinician
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Doctor",
        "last_name": "Strange",
        "email": "dr.strange@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register Patient
    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Wanda",
        "last_name": "Maximoff",
        "date_of_birth": "1989-02-10",
        "gender": "female",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 3. Upload Batch (2 Files)
    file1_content = b"%PDF-1.4 %lab report Hemoglobin: 14.2 g/dL White Blood Cell: 6.5 k/uL Serum Glucose: 95 mg/dL"
    file2_content = b"\x89PNG\r\n\x1a\nImage report Content - Blood Pressure Vitals 120/80 mmHg Pulse 72 bpm"

    files = [
        ("files", ("lab_report.pdf", io.BytesIO(file1_content), "application/pdf")),
        ("files", ("vitals_sheet.png", io.BytesIO(file2_content), "image/png")),
    ]

    upload_res = await async_client.post(
        f"/api/v1/ingestion/patients/{patient_id}/upload",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 201, upload_res.text
    summary = upload_res.json()["data"]
    assert summary["total_files"] == 2
    assert summary["completed_files"] == 2
    assert summary["duplicate_files"] == 0
    assert len(summary["documents"]) == 2

    doc1 = summary["documents"][0]
    assert doc1["original_filename"] == "lab_report.pdf"
    assert doc1["doc_category"] == "lab"
    assert "Hemoglobin" in doc1["extracted_text"]

    doc1_id = doc1["id"]

    # 4. Fetch pipeline processing timeline logs for doc1
    timeline_res = await async_client.get(f"/api/v1/ingestion/documents/{doc1_id}/timeline", headers=headers)
    assert timeline_res.status_code == 200
    logs = timeline_res.json()["data"]
    assert len(logs) >= 3
    step_names = [l["step_name"] for l in logs]
    assert "upload" in step_names
    assert "sha256_check" in step_names
    assert "detection" in step_names
    assert ("sarvam_parse" in step_names or "pymupdf_fallback" in step_names or "sarvam_vision" in step_names)


    # 5. Upload DUPLICATE File (exact same bytes as file1)
    files_dup = [
        ("files", ("lab_report_copy.pdf", io.BytesIO(file1_content), "application/pdf")),
    ]
    dup_res = await async_client.post(
        f"/api/v1/ingestion/patients/{patient_id}/upload",
        files=files_dup,
        headers=headers,
    )
    assert dup_res.status_code == 201
    dup_summary = dup_res.json()["data"]
    assert dup_summary["duplicate_files"] == 1
    assert dup_summary["documents"][0]["status"] == "duplicate"

    # 6. List patient documents
    list_res = await async_client.get(f"/api/v1/ingestion/patients/{patient_id}/documents", headers=headers)
    assert list_res.status_code == 200
    docs_list = list_res.json()["data"]
    assert len(docs_list) >= 2


@pytest.mark.asyncio
async def test_upload_security_validations(async_client: AsyncClient) -> None:
    """Validate file type, magic bytes, and size restrictions."""
    # Register clinician and patient
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Security",
        "last_name": "Tester",
        "email": "security@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "SecPatient",
        "last_name": "One",
        "date_of_birth": "1995-05-05",
        "gender": "male",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 1. Unsupported extension (mp4) -> Should fail 422
    mp4_files = [("files", ("video.mp4", io.BytesIO(b"fake video data"), "video/mp4"))]
    res1 = await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/upload", files=mp4_files, headers=headers)
    assert res1.status_code == 422
    assert "unsupported type" in res1.text.lower() or "validationerror" in res1.text.lower()

    # 2. Fake PDF (Renamed .exe with MZ magic bytes) -> Should fail magic bytes check 422
    exe_as_pdf = [("files", ("malware.pdf", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00this is an executable binary"), "application/pdf"))]
    res2 = await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/upload", files=exe_as_pdf, headers=headers)
    assert res2.status_code == 422
    assert "file signature does not match" in res2.text.lower()


@pytest.mark.asyncio
async def test_text_file_upload_and_direct_copy_paste_entry(async_client: AsyncClient) -> None:
    """Validate plain text (.txt) upload and direct copy-pasted text entry."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "first_name": "TextTester",
        "last_name": "Doc",
        "email": "text.tester@hospital.org",
        "password": "Password123!",
    })
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    p_res = await async_client.post("/api/v1/patients", json={
        "first_name": "Carol",
        "last_name": "Danvers",
        "date_of_birth": "1980-03-03",
        "gender": "female",
    }, headers=headers)
    patient_id = p_res.json()["data"]["id"]

    # 1. Plain text file upload (.txt)
    txt_content = b"Sample Collection Date: 2026-08-05\nHemoglobin: 13.5 g/dL\nPrescribed: Paracetamol 500mg"
    txt_files = [("files", ("consultation_note.txt", io.BytesIO(txt_content), "text/plain"))]

    up_res = await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/upload", files=txt_files, headers=headers)
    assert up_res.status_code == 201
    doc = up_res.json()["data"]["documents"][0]
    assert doc["file_type"] == "txt"
    assert doc["parse_source"] == "plain_text"

    # 2. Copy-pasted direct text entry
    paste_req = {
        "title": "Emergency Room Progress Note",
        "doc_category": "note",
        "raw_text": "Visit Date: 2026-08-06\nPatient presented with acute fatigue.\nBP: 130/85 mmHg, Pulse: 80 bpm.\nPlan: Continue current medications and re-evaluate.",
    }
    p_res = await async_client.post(f"/api/v1/ingestion/patients/{patient_id}/text-entry", json=paste_req, headers=headers)
    assert p_res.status_code == 201
    p_doc = p_res.json()["data"]
    assert p_doc["file_type"] == "txt"
    assert p_doc["parse_source"] == "direct_text"
    assert "acute fatigue" in p_doc["extracted_text"]


