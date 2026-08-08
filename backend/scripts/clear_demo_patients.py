"""
Swasthya — Clear Synthetic Patients Script.

Removes synthetic patients (Arjun Mehta & Priya Sharma)
and their associated physical storage files, documents, timeline events,
lab results, vitals, alerts, and organ scores.

Does NOT affect any real production patients or clinicians.

Usage:
    python scripts/clear_demo_patients.py
"""
import asyncio
import os
import shutil
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import delete, select
from app.database.session import AsyncSessionLocal
from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document, UploadJob, ProcessingLog
from app.modules.timeline.model import TimelineEvent
from app.modules.analytics.model import ParameterHistory
from app.modules.clinical_engine.model import LabResult, VitalSign, ClinicalAlert, OrganScore
from app.modules.medicine_engine.prescription_model import Prescription, PrescriptionMedicine


async def clear_demo_patients() -> None:
    """Find and purge all synthetic dataset records safely."""
    print("=== Swasthya — Clearing Synthetic Dataset ===\n")

    async with AsyncSessionLocal() as session:
        # Find synthetic patients
        stmt = select(Patient).where(
            (Patient.mrn.like("MRN-2026-000%"))
            | (Patient.mrn.like("DEMO-%"))
            | (Patient.notes.like("%longitudinal clinical health profile%"))
            | (Patient.notes.like("%[DEMO DATA]%"))
        )
        res = await session.execute(stmt)
        demo_patients = res.scalars().all()

        if not demo_patients:
            print("✓ No synthetic patients found in database.")
            return

        demo_pids = [p.id for p in demo_patients]
        print(f"Found {len(demo_pids)} synthetic patient(s):")
        for p in demo_patients:
            print(f"  • {p.first_name} {p.last_name} (MRN: {p.mrn}, ID: {p.id[:8]}...)")

        # Get all document IDs belonging to synthetic patients
        doc_stmt = select(Document.id, Document.storage_path, Document.clinician_id, Document.patient_id).where(
            Document.patient_id.in_(demo_pids)
        )
        doc_res = await session.execute(doc_stmt)
        doc_rows = doc_res.all()
        doc_ids = [d.id for d in doc_rows]

        print(f"\nPurging {len(doc_ids)} document(s) & clinical records...")

        # Delete database records in dependency order
        if doc_ids:
            await session.execute(delete(ProcessingLog).where(ProcessingLog.document_id.in_(doc_ids)))

        await session.execute(delete(PrescriptionMedicine).where(PrescriptionMedicine.patient_id.in_(demo_pids)))
        await session.execute(delete(Prescription).where(Prescription.patient_id.in_(demo_pids)))
        await session.execute(delete(ClinicalAlert).where(ClinicalAlert.patient_id.in_(demo_pids)))
        await session.execute(delete(OrganScore).where(OrganScore.patient_id.in_(demo_pids)))
        await session.execute(delete(VitalSign).where(VitalSign.patient_id.in_(demo_pids)))
        await session.execute(delete(LabResult).where(LabResult.patient_id.in_(demo_pids)))
        await session.execute(delete(ParameterHistory).where(ParameterHistory.patient_id.in_(demo_pids)))
        await session.execute(delete(TimelineEvent).where(TimelineEvent.patient_id.in_(demo_pids)))
        await session.execute(delete(UploadJob).where(UploadJob.patient_id.in_(demo_pids)))
        await session.execute(delete(Document).where(Document.patient_id.in_(demo_pids)))
        await session.execute(delete(Patient).where(Patient.id.in_(demo_pids)))

        await session.commit()
        print("✓ Database records purged successfully.")

        # Clean up physical storage directories
        deleted_files = 0
        for doc_id, storage_path, clinician_id, patient_id in doc_rows:
            if storage_path and os.path.exists(storage_path):
                try:
                    os.remove(storage_path)
                    deleted_files += 1
                except Exception as ex:
                    print(f"  ⚠ Failed to delete file {storage_path}: {ex}")

            # Attempt directory cleanup if empty
            if clinician_id and patient_id:
                p_dir = Path("storage/uploads") / clinician_id / patient_id
                if p_dir.exists() and not any(p_dir.iterdir()):
                    try:
                        shutil.rmtree(p_dir)
                    except Exception:
                        pass

        print(f"✓ Deleted {deleted_files} physical storage file(s).")
        print("\n=== Cleanup Complete ===\n")


if __name__ == "__main__":
    asyncio.run(clear_demo_patients())
