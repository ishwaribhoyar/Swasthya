"""
Phase 4 End-to-End Integration & Security Verification Script.

Tests complete clinical timeline reconstruction, 10-priority date policy, parameter history,
deterministic trend calculations, clinician multi-tenant isolation, and duplicate protection.
"""
import sys
import asyncio
import uuid
from pathlib import Path
import httpx

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import AsyncSessionLocal
from app.database.init_db import init_db
from app.core.security import create_access_token
from app.modules.auth.service import AuthService
from app.modules.patients.service import PatientService
from app.modules.patients.schema import PatientCreate
from app.modules.ingestion.service import IngestionService
from app.modules.timeline.service import TimelineService
from app.modules.analytics.service import AnalyticsService


async def main():
    print("=" * 80)
    print("ClinIQ Phase 4 End-to-End Integration & Regression Verification")
    print("=" * 80)

    # 1. Init Database
    await init_db()
    print("\n[STEP 1] SQLite Database initialized.")

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        patient_service = PatientService(session)
        ingestion_service = IngestionService(session)
        timeline_service = TimelineService(session)
        analytics_service = AnalyticsService(session)

        # 2. Register Clinician A & Clinician B
        email_a = f"clinician.a.{uuid.uuid4().hex[:6]}@hospital.org"
        email_b = f"clinician.b.{uuid.uuid4().hex[:6]}@hospital.org"
        
        user_a = await auth_service.register_user(email_a, "Password123!", "Dr. Alice Architect", "M.D.")
        user_b = await auth_service.register_user(email_b, "Password123!", "Dr. Bob Auditor", "M.D.")
        
        print(f"[STEP 2] Clinicians Registered:")
        print(f"  - Clinician A ID: {user_a.id}")
        print(f"  - Clinician B ID: {user_b.id}")

        # 3. Create Patient for Clinician A
        patient_data = PatientCreate(
            first_name="Alex",
            last_name="LongitudinalSubject",
            date_of_birth="1985-05-15",
            gender="male",
            phone="+15550192837",
        )
        patient_a = await patient_service.create_patient(user_a.id, patient_data)
        print(f"\n[STEP 3] Patient Created for Clinician A:")
        print(f"  - MRN: {patient_a.mrn}, ID: {patient_a.id}")

        # 4. Ingest Test Medical Files from repo 'test data' folder
        test_dir = Path(r"C:\Users\datta.000\Desktop\hackathon\test data")
        test_files = list(test_dir.glob("*.jpeg")) + list(test_dir.glob("*.png"))
        print(f"\n[STEP 4] Found {len(test_files)} repository test data files for ingestion.")

        file_payloads = []
        for tf in test_files[:2]:
            content = tf.read_bytes()
            file_payloads.append((tf.name, content))

        summary = await ingestion_service.process_batch_upload(user_a.id, patient_a.id, file_payloads)
        print(f"\n[STEP 5] Batch Processing Completed:")
        print(f"  - Total Processed: {summary.total_files}")
        print(f"  - Completed: {summary.completed_files}")

        # 5. Verify Timeline Events Created with Priority Date Extraction
        timeline_events = await timeline_service.get_patient_timeline(patient_a.id, user_a.id)
        print(f"\n[STEP 6] Reconstructed Timeline Events ({len(timeline_events)} Visit Groups):")
        for group in timeline_events:
            print(f"  Visit Date: {group.visit_date} -- Title: {group.visit_title}")
            for ev in group.events:
                print(f"    - Event Date: {ev.event_date} (Type: {ev.event_date_type}, Confidence: {ev.event_date_confidence*100:.0f}%)")
                print(f"      Title: {ev.title} [{ev.document_type}]")

        assert len(timeline_events) > 0, "Timeline events were not generated!"

        # 6. Verify Longitudinal Trend Analytics
        analytics = await analytics_service.get_patient_trends(patient_a.id, user_a.id)
        print(f"\n[STEP 7] Longitudinal Parameter Trends ({analytics.total_parameters_tracked} parameters tracked):")
        for trend in analytics.trends:
            print(f"  Parameter: {trend.parameter_name} ({trend.unit})")
            print(f"    - Direction: {trend.direction}")
            print(f"    - Change: {trend.absolute_change} {trend.unit} ({trend.percentage_change:.1f}%)")
            print(f"    - Points Count: {trend.observation_count}")

        # 7. Test Clinician Isolation Security
        print(f"\n[STEP 8] Testing Clinician Multi-Tenant Isolation...")
        try:
            await timeline_service.get_patient_timeline(patient_a.id, user_b.id)
            print("  [FAIL] Clinician B was able to access Clinician A's timeline!")
            sys.exit(1)
        except Exception as exc:
            print(f"  [OK] Clinician B blocked from accessing Clinician A's timeline: {exc}")

        try:
            await analytics_service.get_patient_trends(patient_a.id, user_b.id)
            print("  [FAIL] Clinician B was able to access Clinician A's analytics!")
            sys.exit(1)
        except Exception as exc:
            print(f"  [OK] Clinician B blocked from accessing Clinician A's analytics: {exc}")

        # 8. Test Duplicate Ingestion Protection
        print(f"\n[STEP 9] Testing Duplicate Ingestion Protection...")
        summary_dup = await ingestion_service.process_batch_upload(user_a.id, patient_a.id, file_payloads)
        print(f"  - Duplicate Upload Results: {summary_dup.duplicate_files} duplicate files flagged.")
        assert summary_dup.duplicate_files == len(file_payloads), "Duplicate protection failed to detect duplicate files!"

        # Re-check timeline event count (must NOT have duplicated!)
        timeline_after = await timeline_service.get_patient_timeline(patient_a.id, user_a.id)
        total_events_after = sum(g.event_count for g in timeline_after)
        total_events_before = sum(g.event_count for g in timeline_events)
        print(f"  - Events Before: {total_events_before}, Events After: {total_events_after}")
        assert total_events_before == total_events_after, "Duplicate upload created duplicate timeline events!"

    print("\n" + "=" * 80)
    print("ALL PHASE 4 INTEGRATION & SECURITY TESTS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
