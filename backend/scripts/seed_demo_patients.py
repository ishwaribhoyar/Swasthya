"""
Swasthya — Longitudinal Clinical Dataset Seeder.

Creates realistic longitudinal clinical records for Arjun Mehta (Stable)
and Priya Sharma (Progressive High-Risk) across all 5 document categories:
  - Lab Reports
  - Vitals Sheets
  - Prescriptions
  - Discharge Summaries
  - Clinical Notes

Physical files are generated on disk under storage/uploads/{clinician_id}/{patient_id}/{doc_id}.txt
and ingested into SQLite tables (documents, timeline_events, lab_results, parameter_history,
vital_signs, prescriptions, clinical_alerts, organ_scores).

Usage:
    python scripts/seed_demo_patients.py
    python scripts/seed_demo_patients.py --reset
"""
import argparse
import asyncio
import hashlib
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.core.security import get_password_hash
from app.modules.auth.model import User
from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document
from app.modules.timeline.model import TimelineEvent
from app.modules.analytics.model import ParameterHistory
from app.modules.clinical_engine.model import LabResult, VitalSign, ClinicalAlert, OrganScore
from app.modules.clinical_engine.service import ClinicalService
from app.modules.medicine_engine.prescription_model import Prescription, PrescriptionMedicine
from scripts.clear_demo_patients import clear_demo_patients


CLINICIAN_EMAIL = "consultant@swasthya.med"


def utc_dt(year: int, month: int, day: int, hour: int = 9, minute: int = 0) -> datetime:
    """Helper to generate timezone-aware UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


async def get_all_active_clinicians(session) -> list[User]:
    """Get all active clinicians in the database; create consultant account if none exist."""
    stmt = select(User).where(User.is_active == True)
    res = await session.execute(stmt)
    clinicians = list(res.scalars().all())

    # Ensure dedicated consultant clinician also exists
    has_consultant = any(u.email == CLINICIAN_EMAIL for u in clinicians)
    if not has_consultant:
        user = User(
            id=str(uuid.uuid4()),
            email=CLINICIAN_EMAIL,
            password_hash=get_password_hash("ClinicianPassword123!"),
            first_name="Swasthya",
            last_name="Consultant",
            department="Internal Medicine",
            is_active=True,
        )
        session.add(user)
        await session.flush()
        clinicians.append(user)
        print(f"✓ Created Consultant Account: {user.first_name} {user.last_name} ({user.email})")

    print(f"✓ Target clinicians for longitudinal dataset: {len(clinicians)} clinician(s)")
    return clinicians


def create_physical_doc_file(clinician_id: str, patient_id: str, doc_id: str, filename: str, content: str) -> tuple[str, str, int]:
    """
    Write physical file to storage/uploads/{clinician_id}/{patient_id}/{doc_id}.txt
    Returns: (storage_path, sha256_hash, file_size_bytes)
    """
    p_dir = Path("storage/uploads") / clinician_id / patient_id
    p_dir.mkdir(parents=True, exist_ok=True)

    storage_path = str(p_dir / f"{doc_id}.txt")
    file_bytes = content.encode("utf-8")

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()
    return storage_path, sha256_hash, len(file_bytes)


async def seed_patient_a_stable(session, clinician: User) -> Patient:
    """Seed Patient A — Arjun Mehta (Stable / Healthy Longitudinal Trajectory 2021-2026)."""
    mrn = f"MRN-2026-000101-{clinician.id[:4].upper()}"

    patient = Patient(
        id=str(uuid.uuid4()),
        clinician_id=clinician.id,
        created_by=clinician.id,
        mrn=mrn,
        first_name="Arjun",
        last_name="Mehta",
        date_of_birth=date(1981, 3, 14),
        gender="male",
        phone="+91 98765 43210",
        email=f"arjun.mehta.{clinician.id[:6]}@swasthya.med",
        blood_group="O+",
        emergency_contact_name="Ritu Mehta",
        emergency_contact_phone="+91 98765 43211",
        address="42 MG Road, Koramangala, Bengaluru, Karnataka",
        allergies="No known drug allergies (NKDA)",
        chronic_conditions="Mild non-progressive seasonal allergies",
        notes="5-year longitudinal clinical health profile.",
        is_active=True,
    )
    session.add(patient)
    await session.flush()

    # Encounters
    encounters = [
        # 2021
        {"date": utc_dt(2021, 8, 15), "cat": "lab", "type": "Routine Annual Health Check", "hb": 14.8, "wbc": 6800, "plt": 245000, "cr": 0.88, "egfr": 102, "hba1c": 5.2, "glu": 92, "alt": 24, "ast": 22, "crp": 0.9, "sbp": 120, "dbp": 76, "hr": 72, "spo2": 99.0},
        {"date": utc_dt(2021, 8, 16), "cat": "notes", "type": "Annual Physical Wellness Note", "text": "Patient Arjun Mehta examined for routine annual physical. General health excellent. Normal cardiopulmonary exam. Advised routine diet and exercise."},
        {"date": utc_dt(2021, 8, 16), "cat": "prescription", "type": "Preventive Vitamin Supplementation", "meds": [("Multivitamin Daily", "1 tab", "Once daily", "Oral", 30, "With breakfast"), ("Vitamin D3 1000IU", "1 cap", "Once daily", "Oral", 30, "With food")]},
        {"date": utc_dt(2021, 11, 20), "cat": "vitals", "type": "Follow-up Vitals Sheet", "sbp": 118, "dbp": 74, "hr": 70, "spo2": 99.0, "temp": 36.6, "bmi": 23.4},

        # 2022
        {"date": utc_dt(2022, 2, 10), "cat": "notes", "type": "Preventive Consultation Note", "text": "Follow-up check. No complaints. Vitals stable. Patient continues active lifestyle and balanced diet."},
        {"date": utc_dt(2022, 5, 14), "cat": "vitals", "type": "Routine Vitals Sheet", "sbp": 122, "dbp": 76, "hr": 74, "spo2": 98.0, "temp": 36.5, "bmi": 23.6},
        {"date": utc_dt(2022, 8, 18), "cat": "lab", "type": "Annual Comprehensive Metabolic Panel", "hb": 14.9, "wbc": 7000, "plt": 250000, "cr": 0.90, "egfr": 100, "hba1c": 5.3, "glu": 94, "alt": 25, "ast": 23, "crp": 1.0, "sbp": 120, "dbp": 76, "hr": 72, "spo2": 99.0},
        {"date": utc_dt(2022, 8, 19), "cat": "prescription", "type": "Maintenance Prescription", "meds": [("Vitamin D3 1000IU", "1 cap", "Once daily", "Oral", 60, "With food")]},
        {"date": utc_dt(2022, 11, 5), "cat": "vitals", "type": "Quarterly Vitals Log", "sbp": 119, "dbp": 75, "hr": 71, "spo2": 99.0, "temp": 36.6, "bmi": 23.5},

        # 2023
        {"date": utc_dt(2023, 2, 12), "cat": "notes", "type": "Consultation Note - Wellness Review", "text": "Annual review. Arjun Mehta reports regular aerobic exercise and normal sleep patterns. No gastrointestinal or urinary symptoms."},
        {"date": utc_dt(2023, 5, 22), "cat": "discharge", "type": "Day-Care Elective Procedure Summary", "text": "Admission: 2023-05-22 | Discharge: 2023-05-22. Reason: Routine Screening Colonoscopy. Procedure performed without complication. Normal mucosal architecture. Discharged in stable condition."},
        {"date": utc_dt(2023, 8, 20), "cat": "lab", "type": "Annual Executive Health Screening", "hb": 15.0, "wbc": 6600, "plt": 240000, "cr": 0.89, "egfr": 101, "hba1c": 5.3, "glu": 95, "alt": 23, "ast": 21, "crp": 0.8, "sbp": 121, "dbp": 77, "hr": 73, "spo2": 99.0},
        {"date": utc_dt(2023, 8, 21), "cat": "prescription", "type": "Wellness Maintenance Rx", "meds": [("Omega-3 Fish Oil 1000mg", "1 cap", "Once daily", "Oral", 90, "With meals")]},
        {"date": utc_dt(2023, 11, 15), "cat": "vitals", "type": "Vitals Assessment Sheet", "sbp": 120, "dbp": 76, "hr": 70, "spo2": 99.0, "temp": 36.6, "bmi": 23.7},

        # 2024
        {"date": utc_dt(2024, 2, 18), "cat": "notes", "type": "Follow-up Clinical Note", "text": "Patient presents for routine follow-up. Blood pressure optimal. All organ system screening parameters within reference ranges."},
        {"date": utc_dt(2024, 5, 10), "cat": "vitals", "type": "Vitals Record Sheet", "sbp": 122, "dbp": 78, "hr": 75, "spo2": 98.0, "temp": 36.7, "bmi": 23.8},
        {"date": utc_dt(2024, 8, 22), "cat": "lab", "type": "Annual Comprehensive Diagnostic Panel", "hb": 14.7, "wbc": 6900, "plt": 255000, "cr": 0.91, "egfr": 99, "hba1c": 5.4, "glu": 96, "alt": 26, "ast": 24, "crp": 1.1, "sbp": 122, "dbp": 78, "hr": 74, "spo2": 99.0},
        {"date": utc_dt(2024, 8, 23), "cat": "prescription", "type": "Annual Preventive Prescription", "meds": [("Multivitamin Daily", "1 tab", "Once daily", "Oral", 90, "Morning")]},
        {"date": utc_dt(2024, 11, 12), "cat": "vitals", "type": "Routine Vitals Log", "sbp": 120, "dbp": 76, "hr": 72, "spo2": 99.0, "temp": 36.5, "bmi": 23.8},

        # 2025
        {"date": utc_dt(2025, 2, 14), "cat": "notes", "type": "Clinical Progress Consultation", "text": "Annual review for Arjun Mehta. Physical examination unremarkable. Renal and liver profiles stable over 4 years of history."},
        {"date": utc_dt(2025, 5, 16), "cat": "vitals", "type": "Vitals Sheet", "sbp": 121, "dbp": 77, "hr": 73, "spo2": 99.0, "temp": 36.6, "bmi": 23.9},
        {"date": utc_dt(2025, 8, 25), "cat": "lab", "type": "Longitudinal Routine Health Screening", "hb": 14.8, "wbc": 6700, "plt": 248000, "cr": 0.90, "egfr": 100, "hba1c": 5.3, "glu": 93, "alt": 24, "ast": 22, "crp": 0.9, "sbp": 121, "dbp": 77, "hr": 72, "spo2": 99.0},
        {"date": utc_dt(2025, 8, 26), "cat": "prescription", "type": "Maintenance Prescription", "meds": [("Vitamin D3 1000IU", "1 cap", "Once daily", "Oral", 90, "With breakfast")]},
        {"date": utc_dt(2025, 11, 18), "cat": "vitals", "type": "Vitals Tracking Sheet", "sbp": 119, "dbp": 75, "hr": 71, "spo2": 99.0, "temp": 36.6, "bmi": 23.9},

        # 2026
        {"date": utc_dt(2026, 2, 10), "cat": "notes", "type": "Longitudinal Follow-up Clinical Note", "text": "5-year longitudinal review. Patient exhibits consistent hemodynamic stability, normal glycemic markers, and preserved renal function."},
        {"date": utc_dt(2026, 5, 12), "cat": "vitals", "type": "Vitals Sheet", "sbp": 120, "dbp": 76, "hr": 72, "spo2": 99.0, "temp": 36.6, "bmi": 24.0},
        {"date": utc_dt(2026, 8, 8), "cat": "lab", "type": "Current 2026 Annual Laboratory Panel", "hb": 14.9, "wbc": 6800, "plt": 252000, "cr": 0.89, "egfr": 101, "hba1c": 5.3, "glu": 94, "alt": 25, "ast": 23, "crp": 0.9, "sbp": 120, "dbp": 76, "hr": 72, "spo2": 99.0},
        {"date": utc_dt(2026, 8, 8), "cat": "prescription", "type": "Current Active Wellness Prescription", "meds": [("Multivitamin Daily", "1 tab", "Once daily", "Oral", 90, "With breakfast"), ("Omega-3 Fish Oil 1000mg", "1 cap", "Once daily", "Oral", 90, "With meals")]},
    ]

    await process_encounter_list(session, clinician.id, patient.id, encounters, "Arjun Mehta")
    return patient


async def seed_patient_b_progressive(session, clinician: User) -> Patient:
    """Seed Patient B — Priya Sharma (Progressive / High-Risk Longitudinal Trajectory 2021-2026)."""
    mrn = f"MRN-2026-000201-{clinician.id[:4].upper()}"

    patient = Patient(
        id=str(uuid.uuid4()),
        clinician_id=clinician.id,
        created_by=clinician.id,
        mrn=mrn,
        first_name="Priya",
        last_name="Sharma",
        date_of_birth=date(1972, 9, 22),
        gender="female",
        phone="+91 98765 12345",
        email=f"priya.sharma.{clinician.id[:6]}@swasthya.med",
        blood_group="B+",
        emergency_contact_name="Vikram Sharma",
        emergency_contact_phone="+91 98765 12346",
        address="108 Park Street, Indiranagar, Bengaluru, Karnataka",
        allergies="Sulfa drugs (mild rash)",
        chronic_conditions="Progressive Diabetic Nephropathy, Essential Hypertension, Type 2 Diabetes",
        notes="5-year longitudinal clinical health profile showing diabetic nephropathy and hypertension progression.",
        is_active=True,
    )
    session.add(patient)
    await session.flush()

    # Encounters
    encounters = [
        # 2021 — Baseline Normal / Early Borderline
        {"date": utc_dt(2021, 8, 10), "cat": "lab", "type": "Baseline Health Diagnostic Panel", "hb": 13.5, "wbc": 6900, "plt": 240000, "cr": 0.90, "egfr": 88, "hba1c": 5.7, "glu": 98, "alt": 28, "ast": 24, "crp": 1.2, "sbp": 124, "dbp": 78, "hr": 74, "spo2": 98.0},
        {"date": utc_dt(2021, 8, 12), "cat": "notes", "type": "Baseline Consultation Note", "text": "Patient Priya Sharma evaluated for routine baseline health check. Borderline elevated Fasting Glucose (98 mg/dL) and HbA1c (5.7%). Advised lifestyle modification and low glycemic diet."},
        {"date": utc_dt(2021, 11, 15), "cat": "vitals", "type": "Routine Vitals Log", "sbp": 126, "dbp": 80, "hr": 75, "spo2": 98.0, "temp": 36.6, "bmi": 27.2},

        # 2022 — Early Mild Elevation (Metformin Initiated)
        {"date": utc_dt(2022, 2, 18), "cat": "notes", "type": "Follow-up Consultation Note", "text": "Patient reports mild fatigue. Weight increased by 1.5 kg. Blood pressure slightly elevated at 130/82 mmHg."},
        {"date": utc_dt(2022, 5, 20), "cat": "vitals", "type": "Vitals Assessment Log", "sbp": 130, "dbp": 82, "hr": 76, "spo2": 98.0, "temp": 36.6, "bmi": 27.8},
        {"date": utc_dt(2022, 8, 14), "cat": "lab", "type": "Annual Metabolic Review", "hb": 13.1, "wbc": 7100, "plt": 235000, "cr": 1.00, "egfr": 82, "hba1c": 6.0, "glu": 108, "alt": 32, "ast": 27, "crp": 1.8, "sbp": 130, "dbp": 82, "hr": 76, "spo2": 98.0},
        {"date": utc_dt(2022, 8, 15), "cat": "prescription", "type": "Antidiabetic Initiation Prescription", "meds": [("Metformin HCl 500mg", "1 tab", "Once daily", "Oral", 90, "With dinner")]},
        {"date": utc_dt(2022, 11, 22), "cat": "vitals", "type": "Quarterly Vitals Sheet", "sbp": 134, "dbp": 84, "hr": 78, "spo2": 97.0, "temp": 36.7, "bmi": 28.1},

        # 2023 — Moderate Progression (Antihypertensive Telmisartan Added)
        {"date": utc_dt(2023, 2, 15), "cat": "notes", "type": "Clinical Progress Note", "text": "Persistent blood pressure elevation (138/86 mmHg) and rising HbA1c (6.4%). Serum Creatinine increased to 1.15 mg/dL. Initiating Telmisartan 40mg daily for BP and renal protection."},
        {"date": utc_dt(2023, 5, 18), "cat": "vitals", "type": "Vitals Log", "sbp": 138, "dbp": 86, "hr": 80, "spo2": 97.0, "temp": 36.6, "bmi": 28.5},
        {"date": utc_dt(2023, 8, 16), "cat": "lab", "type": "Comprehensive Renal & Metabolic Panel", "hb": 12.4, "wbc": 7400, "plt": 225000, "cr": 1.18, "egfr": 72, "hba1c": 6.4, "glu": 118, "alt": 35, "ast": 29, "crp": 2.6, "sbp": 138, "dbp": 86, "hr": 78, "spo2": 97.0},
        {"date": utc_dt(2023, 8, 17), "cat": "prescription", "type": "Dual Therapy Escalation Rx", "meds": [("Metformin HCl 500mg", "1 tab", "Twice daily (BID)", "Oral", 90, "After meals"), ("Telmisartan 40mg", "1 tab", "Once daily", "Oral", 90, "Morning")]},
        {"date": utc_dt(2023, 11, 25), "cat": "vitals", "type": "Outpatient Vitals Record", "sbp": 142, "dbp": 88, "hr": 82, "spo2": 97.0, "temp": 36.7, "bmi": 28.9},

        # 2024 — Stage 2-3 CKD & Hypertensive Inpatient Evaluation
        {"date": utc_dt(2024, 2, 10), "cat": "notes", "type": "Nephrology Consultation Note", "text": "Patient exhibits progressive decline in eGFR (61 mL/min/1.73m²) and serum creatinine rise to 1.35 mg/dL. Microalbuminuria present. Diagnosis: Stage 2-3 Chronic Kidney Disease secondary to Diabetic Nephropathy."},
        {"date": utc_dt(2024, 5, 14), "cat": "vitals", "type": "Pre-Admission Vitals Log", "sbp": 146, "dbp": 90, "hr": 84, "spo2": 96.0, "temp": 36.8, "bmi": 29.2},
        {"date": utc_dt(2024, 6, 12), "cat": "discharge", "type": "Inpatient Discharge Summary - Hypertensive Urgency", "text": "Admission: 2024-06-10 | Discharge: 2024-06-12. Reason for Admission: Acute hypertensive urgency (BP 158/98 mmHg) and headache. Course: Stabilized with IV labetalol and oral Telmisartan dose adjustment to 80mg daily. Renal parameters monitored. Discharged in stable condition with outpatient nephrology follow-up."},
        {"date": utc_dt(2024, 8, 18), "cat": "lab", "type": "Post-Discharge Renal & Lipid Diagnostic Panel", "hb": 11.2, "wbc": 7800, "plt": 215000, "cr": 1.38, "egfr": 61, "hba1c": 6.9, "glu": 132, "alt": 38, "ast": 31, "crp": 3.8, "sbp": 146, "dbp": 90, "hr": 82, "spo2": 96.0},
        {"date": utc_dt(2024, 8, 19), "cat": "prescription", "type": "Post-Discharge Escalated Regimen Rx", "meds": [("Metformin HCl 1000mg", "1 tab", "Twice daily (BID)", "Oral", 90, "With meals"), ("Telmisartan 80mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Atorvastatin 20mg", "1 tab", "Once daily", "Oral", 90, "Bedtime")]},
        {"date": utc_dt(2024, 11, 20), "cat": "vitals", "type": "Vitals Monitoring Log", "sbp": 148, "dbp": 92, "hr": 83, "spo2": 96.0, "temp": 36.7, "bmi": 29.5},

        # 2025 — Stage 3a CKD Progression & Glycemic Deterioration
        {"date": utc_dt(2025, 2, 12), "cat": "notes", "type": "Specialist Follow-up Note", "text": "Serum creatinine increased to 1.55 mg/dL; eGFR reduced to 52 mL/min. Patient notes bilateral ankle edema. Metformin dose reduced due to renal function; Linagliptin 5mg added."},
        {"date": utc_dt(2025, 5, 18), "cat": "vitals", "type": "Clinical Vitals Log", "sbp": 152, "dbp": 94, "hr": 85, "spo2": 96.0, "temp": 36.8, "bmi": 29.8},
        {"date": utc_dt(2025, 6, 20), "cat": "discharge", "type": "Inpatient Episode Summary - Acute Kidney Stress", "text": "Admission: 2025-06-18 | Discharge: 2025-06-20. Reason: Acute kidney stress secondary to gastroenteritis & volume depletion. Creatinine peaked at 1.72 mg/dL, improved to 1.55 mg/dL following rehydration. Discharged with adjusted antihypertensive therapy."},
        {"date": utc_dt(2025, 8, 22), "cat": "lab", "type": "Comprehensive 2025 Renal & Inflammatory Panel", "hb": 10.1, "wbc": 8200, "plt": 205000, "cr": 1.58, "egfr": 52, "hba1c": 7.3, "glu": 145, "alt": 42, "ast": 35, "crp": 4.9, "sbp": 152, "dbp": 94, "hr": 84, "spo2": 96.0},
        {"date": utc_dt(2025, 8, 23), "cat": "prescription", "type": "Renal-Adjusted Triple Therapy Rx", "meds": [("Linagliptin 5mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Telmisartan 80mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Amlodipine 5mg", "1 tab", "Once daily", "Oral", 90, "Evening"), ("Atorvastatin 20mg", "1 tab", "Once daily", "Oral", 90, "Bedtime")]},
        {"date": utc_dt(2025, 11, 15), "cat": "vitals", "type": "Vitals Log", "sbp": 154, "dbp": 95, "hr": 86, "spo2": 95.0, "temp": 36.8, "bmi": 30.1},

        # 2026 — Stage 3b CKD, Anemia & High-Risk Inflammatory Strain (Current)
        {"date": utc_dt(2026, 2, 15), "cat": "notes", "type": "Current Nephrology Progress Note", "text": "5-year longitudinal evaluation confirms progressive Stage 3b CKD (eGFR 44 mL/min, Creatinine 1.78 mg/dL) and worsening normocytic anemia (Hb 9.2 g/dL). Inflammatory markers elevated (CRP 6.3 mg/L). Blood pressure remains suboptimally controlled at 158/96 mmHg."},
        {"date": utc_dt(2026, 5, 20), "cat": "vitals", "type": "Vitals Tracking Sheet", "sbp": 156, "dbp": 95, "hr": 85, "spo2": 95.0, "temp": 36.7, "bmi": 30.3},
        {"date": utc_dt(2026, 8, 8), "cat": "lab", "type": "Current 2026 Comprehensive Diagnostic Panel", "hb": 9.2, "wbc": 8500, "plt": 198000, "cr": 1.78, "egfr": 44, "hba1c": 7.6, "glu": 158, "alt": 45, "ast": 38, "crp": 6.3, "sbp": 158, "dbp": 96, "hr": 86, "spo2": 95.0},
        {"date": utc_dt(2026, 8, 8), "cat": "prescription", "type": "Current Active High-Risk Regimen Rx", "meds": [("Linagliptin 5mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Telmisartan 80mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Amlodipine 5mg", "1 tab", "Once daily", "Oral", 90, "Evening"), ("Chlorthalidone 12.5mg", "1 tab", "Once daily", "Oral", 90, "Morning"), ("Atorvastatin 40mg", "1 tab", "Once daily", "Oral", 90, "Bedtime")]},
    ]

    await process_encounter_list(session, clinician.id, patient.id, encounters, "Priya Sharma")
    return patient


async def process_encounter_list(session, clinician_id: str, patient_id: str, encounters: list, patient_name: str) -> None:
    """Helper to process and write physical files & database rows for an encounter list."""
    for idx, enc in enumerate(encounters, 1):
        doc_id = str(uuid.uuid4())
        dt = enc["date"]
        dt_str = dt.strftime("%Y-%m-%d")
        category = enc["cat"]
        title = enc["type"]

        content_lines = [
            f"SWASTHYA MEDICAL RECORD — {title.upper()}",
            f"Patient Name: {patient_name}",
            f"Document ID: {doc_id}",
            f"Date of Record: {dt_str}",
            f"Category: {category.upper()}",
            "=" * 60,
            "",
        ]

        if category == "lab":
            content_lines.extend([
                "LABORATORY TEST RESULTS:",
                f"  • Hemoglobin: {enc['hb']} g/dL (Ref: 12.0 - 17.5 g/dL)",
                f"  • WBC: {enc['wbc']} /uL (Ref: 4500 - 11000 /uL)",
                f"  • Platelets: {enc['plt']} /uL (Ref: 150000 - 450000 /uL)",
                f"  • Serum Creatinine: {enc['cr']} mg/dL (Ref: 0.6 - 1.2 mg/dL)",
                f"  • eGFR: {enc['egfr']} mL/min/1.73m2 (Ref: > 90 mL/min)",
                f"  • HbA1c: {enc['hba1c']} % (Ref: 4.0 - 5.6 %)",
                f"  • Fasting Glucose: {enc['glu']} mg/dL (Ref: 70 - 99 mg/dL)",
                f"  • ALT: {enc['alt']} U/L (Ref: 7 - 56 U/L)",
                f"  • AST: {enc['ast']} U/L (Ref: 8 - 40 U/L)",
                f"  • CRP: {enc['crp']} mg/L (Ref: < 3.0 mg/L)",
            ])
        elif category == "vitals":
            content_lines.extend([
                "VITAL SIGNS SHEET:",
                f"  • Blood Pressure: {enc['sbp']}/{enc['dbp']} mmHg",
                f"  • Heart Rate: {enc['hr']} bpm",
                f"  • SpO2: {enc['spo2']} %",
                f"  • Temperature: {enc.get('temp', 36.6)} °C",
                f"  • BMI: {enc.get('bmi', 24.0)} kg/m2",
            ])
        elif category == "prescription":
            content_lines.extend([
                "PRESCRIPTION DETAILS:",
            ])
            for med_name, dose, freq, route, dur, inst in enc["meds"]:
                content_lines.append(f"  • {med_name} — Dose: {dose}, Freq: {freq}, Route: {route}, Duration: {dur} days ({inst})")
        elif category in ("notes", "discharge"):
            content_lines.extend([
                "CLINICAL SUMMARY & OBSERVATIONS:",
                enc["text"],
            ])

        full_content = "\n".join(content_lines)
        filename = f"{patient_name.replace(' ', '_')}_{category}_{dt_str}.txt"

        storage_path, sha256_hash, file_size = create_physical_doc_file(
            clinician_id, patient_id, doc_id, filename, full_content
        )

        doc = Document(
            id=doc_id,
            patient_id=patient_id,
            clinician_id=clinician_id,
            original_filename=filename,
            storage_path=storage_path,
            mime_type="text/plain",
            file_type="TXT",
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            status="completed",
            extracted_text=full_content,
            extracted_markdown=full_content,
            doc_category=category,
            document_date=dt,
            confidence_score=0.98,
            parse_source="direct_text",
            created_at=dt,
        )
        session.add(doc)
        await session.flush()

        te = TimelineEvent(
            patient_id=patient_id,
            clinician_id=clinician_id,
            record_id=doc_id,
            event_date=dt,
            date_priority_source="document_date",
            event_type=category if category != "lab" else "lab_report",
            document_type="TXT",
            title=f"{title} ({dt_str})",
            summary=full_content[:300],
            confidence=0.98,
            created_at=dt,
        )
        session.add(te)

        if category == "lab":
            lab_params = [
                ("Serum Creatinine", enc["cr"], "mg/dL", 0.6, 1.2, "HIGH" if enc["cr"] > 1.2 else "NORMAL"),
                ("eGFR", enc["egfr"], "mL/min/1.73m²", 60.0, 120.0, "LOW" if enc["egfr"] < 60 else "NORMAL"),
                ("HbA1c", enc["hba1c"], "%", 4.0, 5.6, "HIGH" if enc["hba1c"] > 5.6 else "NORMAL"),
                ("Fasting Glucose", enc["glu"], "mg/dL", 70.0, 99.0, "HIGH" if enc["glu"] > 99 else "NORMAL"),
                ("Hemoglobin", enc["hb"], "g/dL", 12.0, 17.5, "LOW" if enc["hb"] < 12.0 else "NORMAL"),
                ("CRP", enc["crp"], "mg/L", 0.0, 3.0, "HIGH" if enc["crp"] > 3.0 else "NORMAL"),
            ]

            for pname, pval, punit, rmin, rmax, pstatus in lab_params:
                ph = ParameterHistory(
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    record_id=doc_id,
                    parameter_name=pname,
                    normalized_name=pname.lower().replace(" ", "_"),
                    value=float(pval),
                    value_str=f"{pval}",
                    unit=punit,
                    reference_range=f"{rmin} - {rmax}",
                    status=pstatus,
                    event_date=dt,
                    confidence=0.98,
                    created_at=dt,
                )
                session.add(ph)

                lr = LabResult(
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    document_id=doc_id,
                    test_name=pname,
                    test_code=pname.lower().replace(" ", "_"),
                    numeric_value=float(pval),
                    unit=punit,
                    ref_min=rmin,
                    ref_max=rmax,
                    status=pstatus,
                    confidence_score=0.98,
                    tested_at=dt,
                    created_at=dt,
                )
                session.add(lr)

        elif category == "vitals":
            vs = VitalSign(
                patient_id=patient_id,
                clinician_id=clinician_id,
                document_id=doc_id,
                sbp=enc["sbp"],
                dbp=enc["dbp"],
                heart_rate=enc["hr"],
                spo2=enc["spo2"],
                temperature_c=enc.get("temp", 36.6),
                bmi=enc.get("bmi", 24.0),
                status="HIGH" if enc["sbp"] >= 140 or enc["dbp"] >= 90 else "NORMAL",
                recorded_at=dt,
                created_at=dt,
            )
            session.add(vs)

        elif category == "prescription":
            rx = Prescription(
                patient_id=patient_id,
                clinician_id=clinician_id,
                document_id=doc_id,
                prescribed_by="Dr. Swasthya Consultant",
                prescription_date=dt,
                notes=title,
                created_at=dt,
            )
            session.add(rx)
            await session.flush()

            for med_name, dose, freq, route, dur, inst in enc["meds"]:
                strength = med_name.split()[-1] if any(c.isdigit() for c in med_name) else "Standard"
                pm = PrescriptionMedicine(
                    prescription_id=rx.id,
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    medicine_name=med_name,
                    strength=strength,
                    dose=dose,
                    frequency=freq,
                    route=route,
                    duration_days=dur,
                    instructions=inst,
                    created_at=dt,
                )
                session.add(pm)

    await session.flush()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Swasthya Longitudinal Clinical Dataset Seeder")
    parser.add_argument("--reset", action="store_true", help="Clear existing synthetic dataset before seeding")
    args = parser.parse_args()

    if args.reset:
        await clear_demo_patients()

    print("=== Swasthya — Seeding Longitudinal Clinical Dataset for ALL Clinicians ===\n")

    async with AsyncSessionLocal() as session:
        clinicians = await get_all_active_clinicians(session)
        clinical_svc = ClinicalService(session)

        for c_idx, clinician in enumerate(clinicians, 1):
            print(f"\n--- [{c_idx}/{len(clinicians)}] Seeding for Clinician: {clinician.first_name} {clinician.last_name} ({clinician.email}) ---")

            pat_a = await seed_patient_a_stable(session, clinician)
            pat_b = await seed_patient_b_progressive(session, clinician)

            await session.commit()

            # Run Clinical Intelligence Analysis Engine
            await clinical_svc.analyze_patient(pat_a.id, clinician.id)
            await clinical_svc.analyze_patient(pat_b.id, clinician.id)
            await session.commit()
            print(f"  ✓ Arjun Mehta & Priya Sharma ready for clinician {clinician.email}")

    print("\n============================================================")
    print("  ✓ LONGITUDINAL CLINICAL DATASET SEEDING COMPLETE")
    print("============================================================")
    print(f"  Clinicians Seeded: {len(clinicians)}")
    print(f"  Patients per Clinician:")
    print(f"    • Arjun Mehta (MRN: MRN-2026-000101-*) — STABLE")
    print(f"    • Priya Sharma (MRN: MRN-2026-000201-*) — PROGRESSIVE HIGH-RISK")
    print("============================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
