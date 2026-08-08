"""
Database Re-Analysis Script.

Recreates organ_scores table with nullable score column, purges stale clinical alerts,
and re-analyzes all patients using the updated OrganScoringEngine (8-systems, score=None for insufficient data)
and AlertEngine (decision support without prescriptive drug instructions).
"""
import sys
import asyncio
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, delete, text
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base

# Import ALL SQLAlchemy models to register table schemas
from app.modules.auth.model import User
from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document
from app.modules.clinical_engine.model import LabResult, VitalSign, OrganScore, ClinicalAlert
from app.modules.clinical_engine.service import ClinicalService


async def main():
    print("=" * 80)
    print("Re-analyzing All Existing Database Patients")
    print("=" * 80)

    # Recreate organ_scores table to update column NULL constraint in SQLite
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS organ_scores"))
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Recreated organ_scores table with nullable score column.")

    async with AsyncSessionLocal() as session:
        # Fetch all patients
        res = await session.execute(select(Patient))
        patients = res.scalars().all()

        print(f"Found {len(patients)} patients in SQLite database.")

        # Purge stale clinical alerts
        await session.execute(delete(ClinicalAlert))
        await session.commit()
        print("Purged old clinical alerts from database.")

        clinical_service = ClinicalService(session)

        for p in patients:
            print(f"\nRe-analyzing Patient: {p.first_name} {p.last_name} (ID: {p.id}, MRN: {p.mrn})")

            overview = await clinical_service.analyze_patient(p.id, p.clinician_id)
            print(f"  - Analyzed Documents: {overview.analyzed_documents_count}")
            print(f"  - Generated Alerts: {len(overview.alerts)}")
            for a in overview.alerts:
                print(f"    * Alert: {a.title}")
                print(f"      Action: {a.action_recommendation}")
            
            print(f"  - 8-Organ System Scores:")
            for s in overview.organ_scores:
                score_str = f"{s.score}%" if s.score is not None else "None (INSUFFICIENT_DATA)"
                print(f"    * {s.organ_system.title()}: {score_str} [{s.status}]")

    print("\n" + "=" * 80)
    print("DATABASE RE-ANALYSIS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
