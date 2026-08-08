"""
Tests for Patients module.
Validates multi-tenant clinician data isolation, sequential MRN generation,
soft-delete & restore, statistics, and search/sort/filter.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patient_crud_and_isolation_flow(async_client: AsyncClient) -> None:
    """Test complete patient lifecycle and multi-clinician data isolation."""
    # 1. Register Clinician A
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@hospital.org",
        "password": "Password123!",
    })
    token_a = reg_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register Clinician B
    reg_b = await async_client.post("/api/v1/auth/register", json={
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob.jones@hospital.org",
        "password": "Password123!",
    })
    token_b = reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Clinician A registers Patient 1
    p1_payload = {
        "first_name": "Robert",
        "last_name": "Johnson",
        "date_of_birth": "1980-05-15",
        "gender": "male",
        "phone": "+15551234567",
        "blood_group": "O+",
        "allergies": "Penicillin",
        "chronic_conditions": "Hypertension",
        "notes": "Initial consultation."
    }
    create1 = await async_client.post("/api/v1/patients", json=p1_payload, headers=headers_a)
    assert create1.status_code == 201, create1.text
    p1 = create1.json()["data"]
    assert p1["first_name"] == "Robert"
    assert p1["mrn"].startswith("MRN-")
    p1_id = p1["id"]

    # 4. Clinician A registers Patient 2 — verify sequential MRN
    p2_payload = {
        "first_name": "Emma",
        "last_name": "Watson",
        "date_of_birth": "1990-04-15",
        "gender": "female",
        "blood_group": "A+",
    }
    create2 = await async_client.post("/api/v1/patients", json=p2_payload, headers=headers_a)
    assert create2.status_code == 201
    p2 = create2.json()["data"]

    seq1 = int(p1["mrn"].split("-")[-1])
    seq2 = int(p2["mrn"].split("-")[-1])
    assert seq2 == seq1 + 1, f"Expected sequential MRN, got {p1['mrn']} and {p2['mrn']}"

    # 5. Clinician B lists patients — should see 0 patients
    list_b = await async_client.get("/api/v1/patients", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["data"]["total"] == 0

    # 6. Clinician B attempts to access Clinician A's patient — should return 404
    get_b = await async_client.get(f"/api/v1/patients/{p1_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 7. Clinician A checks statistics
    stats_a = await async_client.get("/api/v1/patients/statistics", headers=headers_a)
    assert stats_a.status_code == 200
    sdata = stats_a.json()["data"]
    assert sdata["total_patients"] == 2
    assert sdata["active_patients"] == 2
    assert sdata["archived_patients"] == 0
    assert sdata["gender_distribution"]["male"] == 1
    assert sdata["gender_distribution"]["female"] == 1

    # 8. Clinician A updates Patient 1
    update_res = await async_client.patch(
        f"/api/v1/patients/{p1_id}",
        json={"notes": "Updated clinical notes."},
        headers=headers_a
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["notes"] == "Updated clinical notes."

    # 9. Clinician A archives Patient 1 (Soft delete)
    archive_res = await async_client.delete(f"/api/v1/patients/{p1_id}", headers=headers_a)
    assert archive_res.status_code == 200
    assert archive_res.json()["data"]["is_active"] is False

    # 10. Clinician A lists active patients — should see only 1
    list_active = await async_client.get("/api/v1/patients", headers=headers_a)
    assert list_active.json()["data"]["total"] == 1

    # 11. Clinician A lists with include_archived=true — should see 2
    list_all = await async_client.get("/api/v1/patients?include_archived=true", headers=headers_a)
    assert list_all.json()["data"]["total"] == 2

    # 12. Clinician A restores Patient 1
    restore_res = await async_client.post(f"/api/v1/patients/{p1_id}/restore", headers=headers_a)
    assert restore_res.status_code == 200
    assert restore_res.json()["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_foreign_key_enforcement(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Verify that SQLite Foreign Key enforcement (PRAGMA foreign_keys = ON) prevents orphan records."""
    from sqlalchemy.exc import IntegrityError
    from app.modules.patients.model import Patient
    from datetime import date

    invalid_patient = Patient(
        clinician_id="00000000-0000-0000-0000-000000000000",  # Non-existent user
        created_by="00000000-0000-0000-0000-000000000000",
        mrn="MRN-TEST-FK",
        first_name="Orphan",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
        gender="male",
    )

    db_session.add(invalid_patient)
    with pytest.raises(IntegrityError) as exc_info:
        await db_session.commit()

    assert "FOREIGN KEY constraint failed" in str(exc_info.value)


