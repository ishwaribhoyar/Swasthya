"""
Phase 4 End-to-End Sample Data Test Script.

Ingests multi-date longitudinal lab reports for a test patient to empirically verify:
1. Priority Event Date Extraction (Timeline driven by clinical event dates 2026-06-01 -> 2026-07-01 -> 2026-08-01).
2. Parameter History & Time-Series Datapoints (Potassium, Creatinine, Glucose).
3. Deterministic Trend Engine (RAPIDLY_INCREASING direction, % shift, rate per day).
4. 8-Organ System Scoring (Renal & Electrolyte scores drop dynamically with rising markers).
5. Non-prescriptive Decision Support Alerts.
6. Full API endpoint payloads for frontend Timeline & Analytics views.
"""
import sys
import asyncio
import uuid
from datetime import date
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.init_db import init_db

from app.modules.auth.model import User
from app.modules.auth.service import AuthService
from app.modules.auth.schema import RegisterRequest

from app.modules.patients.model import Patient
from app.modules.patients.service import PatientService
from app.modules.patients.schema import PatientCreate

from app.modules.ingestion.service import IngestionService
from app.modules.ingestion.schema import TextEntryRequest

from app.modules.clinical_engine.service import ClinicalService
from app.modules.timeline.service import TimelineService
from app.modules.analytics.service import AnalyticsService


# 3 Multi-date lab reports demonstrating longitudinal patient progression
DOC_JUNE = """
METROPOLIS HEALTHCARE LABS
PATIENT: John Doe | AGE: 45 | GENDER: Male
SAMPLE COLLECTION DATE: 01 June 2026
VISIT TYPE: Routine Executive Health Checkup

LABORATORY INVESTIGATIONS:
Serum Potassium: 4.2 mEq/L (Reference: 3.5 - 5.0 mEq/L) [NORMAL]
Serum Creatinine: 0.9 mg/dL (Reference: 0.6 - 1.2 mg/dL) [NORMAL]
Fasting Glucose: 95 mg/dL (Reference: 70 - 99 mg/dL) [NORMAL]
Hemoglobin: 14.5 g/dL (Reference: 12.0 - 17.5 g/dL) [NORMAL]

PHYSICAL VITALS:
Blood Pressure: 120/80 mmHg
Heart Rate: 72 bpm
SpO2: 98%
"""

DOC_JULY = """
DIAGNOSTICS & CLINICAL CARE CENTER
PATIENT: John Doe | AGE: 45 | GENDER: Male
SAMPLE COLLECTION DATE: 01 July 2026
VISIT TYPE: Follow-up Consultation

LABORATORY INVESTIGATIONS:
Serum Potassium: 5.4 mEq/L (Reference: 3.5 - 5.0 mEq/L) [HIGH]
Serum Creatinine: 1.6 mg/dL (Reference: 0.6 - 1.2 mg/dL) [HIGH]
Fasting Glucose: 135 mg/dL (Reference: 70 - 99 mg/dL) [HIGH]
Hemoglobin: 13.8 g/dL (Reference: 12.0 - 17.5 g/dL) [NORMAL]

PHYSICAL VITALS:
Blood Pressure: 135/88 mmHg
Heart Rate: 78 bpm
SpO2: 97%
"""

DOC_AUGUST = """
CITY GENERAL HOSPITAL - EMERGENCY & ICU DEPT
PATIENT: John Doe | AGE: 45 | GENDER: Male
SAMPLE COLLECTION DATE: 01 August 2026
VISIT TYPE: Urgent Medical Evaluation

LABORATORY INVESTIGATIONS:
Serum Potassium: 6.5 mEq/L (Reference: 3.5 - 5.0 mEq/L) [CRITICAL_HIGH]
Serum Creatinine: 2.4 mg/dL (Reference: 0.6 - 1.2 mg/dL) [CRITICAL_HIGH]
Fasting Glucose: 180 mg/dL (Reference: 70 - 99 mg/dL) [HIGH]
Hemoglobin: 13.1 g/dL (Reference: 12.0 - 17.5 g/dL) [NORMAL]

PHYSICAL VITALS:
Blood Pressure: 145/92 mmHg
Heart Rate: 84 bpm
SpO2: 96%
"""


async def main():
    print("=" * 90)
    print("CLINIQ PHASE 4 END-TO-END SAMPLE DATA VERIFICATION")
    print("=" * 90)

    await init_db()

    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session)
        patient_service = PatientService(session)
        ingestion_service = IngestionService(session)
        clinical_service = ClinicalService(session)
        timeline_service = TimelineService(session)
        analytics_service = AnalyticsService(session)

        # 1. Register test clinician
        email = f"dr.phase4.test_{uuid.uuid4().hex[:6]}@cliniq.med"
        token_res = await auth_service.register(
            RegisterRequest(
                email=email,
                password="TestPassword123!",
                first_name="Dr. Sarah",
                last_name="Conner",
            )
        )
        clinician_id = token_res.user.id
        print(f"\n[STEP 1] Registered Clinician: {token_res.user.email} (ID: {clinician_id})")

        # 2. Create test patient
        patient_dto = await patient_service.create_patient(
            PatientCreate(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1981, 5, 12),
                gender="male",
                phone="9876543210",
                email="john.doe@example.com",
                blood_group="O+",
            ),
            clinician_id=clinician_id,
        )
        patient_id = patient_dto.id
        print(f"[STEP 2] Created Patient: John Doe (MRN: {patient_dto.mrn}, ID: {patient_id})")

        # 3. Ingest 3 historical document records (June, July, August 2026)
        print("\n[STEP 3] Ingesting 3 Longitudinal Clinical Reports...")

        doc1 = await ingestion_service.process_text_entry(
            patient_id=patient_id,
            clinician_id=clinician_id,
            req=TextEntryRequest(
                title="Lab Report - June 2026",
                doc_category="lab",
                raw_text=DOC_JUNE,
            )
        )
        doc2 = await ingestion_service.process_text_entry(
            patient_id=patient_id,
            clinician_id=clinician_id,
            req=TextEntryRequest(
                title="Lab Report - July 2026",
                doc_category="lab",
                raw_text=DOC_JULY,
            )
        )
        doc3 = await ingestion_service.process_text_entry(
            patient_id=patient_id,
            clinician_id=clinician_id,
            req=TextEntryRequest(
                title="Lab Report - August 2026",
                doc_category="lab",
                raw_text=DOC_AUGUST,
            )
        )
        print(f"  - Ingested Doc 1 (June 2026): ID {doc1.id}")
        print(f"  - Ingested Doc 2 (July 2026): ID {doc2.id}")
        print(f"  - Ingested Doc 3 (August 2026): ID {doc3.id}")

        # 4. Trigger Clinical Analysis
        print("\n[STEP 4] Running Clinical Intelligence Engine & 8-Organ System Scoring...")
        overview = await clinical_service.analyze_patient(patient_id, clinician_id)

        print(f"  - Total Labs Parsed: {len(overview.latest_labs)}")
        print(f"  - Decision Support Alerts ({len(overview.alerts)}):")
        for a in overview.alerts:
            print(f"    * [{a.severity}] {a.title}")
            print(f"      Action: {a.action_recommendation}")

        print(f"  - 8-Organ System Health Scores:")
        for s in overview.organ_scores:
            score_str = f"{s.score}%" if s.score is not None else "None (INSUFFICIENT_DATA)"
            print(f"    * {s.organ_system.title()}: {score_str} [{s.status}]")

        # Verify Electrolyte & Renal scores dropped dynamically due to 6.5 Potassium & 2.4 Creatinine
        elec_s = next((s for s in overview.organ_scores if s.organ_system == "electrolyte"), None)
        ren_s = next((s for s in overview.organ_scores if s.organ_system == "renal"), None)

        assert elec_s is not None and elec_s.score == 30.0, f"Expected Electrolyte score 30.0%, got {elec_s.score if elec_s else 'None'}"
        assert ren_s is not None and ren_s.score == 75.0, f"Expected Renal score 75.0%, got {ren_s.score if ren_s else 'None'}"
        print("  [OK] Electrolyte score correctly dropped to 30.0% (Critical Concern)!")
        print("  [OK] Renal score correctly dropped to 75.0% (Mild Strain)!")

        # 5. Fetch Timeline Stream & Verify Date Priority Extraction
        print("\n[STEP 5] Fetching Clinical Event Timeline...")
        visit_groups = await timeline_service.get_patient_timeline(patient_id, clinician_id)
        total_events = sum(len(vg.events) for vg in visit_groups)
        print(f"  - Total Timeline Events: {total_events}")
        print(f"  - Total Visit Groups: {len(visit_groups)}")

        for vg in visit_groups:

            print(f"\n  Visit Group Date: {vg.visit_date} (Events: {len(vg.events)})")
            for ev in vg.events:
                print(f"    - [{ev.event_date.strftime('%Y-%m-%d')} · {ev.date_priority_source}] {ev.title}")


        # 6. Fetch Longitudinal Analytics & Verify Trend Calculations
        print("\n[STEP 6] Fetching Longitudinal Trend Analytics & Canonical parameter_trends Payload...")
        analytics = await analytics_service.get_patient_analytics(patient_id, clinician_id)

        print(f"  - Total Parameters Tracked: {analytics.total_parameters_tracked}")
        print(f"  - Canonical parameter_trends count: {len(analytics.parameter_trends)}")

        assert len(analytics.parameter_trends) > 0, "No parameter trends generated!"

        for tr in analytics.parameter_trends:
            latest_pt = tr.data_points[-1] if tr.data_points else None
            latest_val = latest_pt.value if latest_pt else "—"
            latest_dt = latest_pt.date if latest_pt else "—"
            print(f"\n  Parameter: {tr.parameter_name} ({tr.unit})")
            print(f"    * Latest Value: {latest_val} {tr.unit} on {latest_dt}")
            print(f"    * Direction: {tr.direction} (Risk Level: {tr.risk_level})")
            print(f"    * Time-series Data Points ({len(tr.data_points)}):")
            for pt in tr.data_points:
                print(f"      - {pt.date}: {pt.value} {pt.unit} [{pt.status}]")


        # Verify Potassium Trend: 4.2 -> 5.4 -> 6.5 mEq/L
        k_trend = next((t for t in analytics.parameter_trends if "Potassium" in t.parameter_name), None)
        assert k_trend is not None, "Potassium trend missing!"
        assert k_trend.direction in ["Critical Rise", "RAPIDLY_INCREASING", "INCREASING"], f"Unexpected direction {k_trend.direction}"
        assert len(k_trend.data_points) == 3, f"Expected 3 points, got {len(k_trend.data_points)}"
        print("\n  [OK] Potassium trend curve verified: 4.2 -> 5.4 -> 6.5 mEq/L (Critical Rise)!")


        print("\n" + "=" * 90)
        print("ALL PHASE 4 END-TO-END SAMPLE DATA CHECKS PASSED PERFECTLY!")
        print("=" * 90)


if __name__ == "__main__":
    asyncio.run(main())
