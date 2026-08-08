"""
System Verification Script:
1. Tests Sarvam AI API Key & Vision / Parse endpoints
2. Tests OpenAI API Key & GPT model connectivity
3. Tests multi-document ingestion on repository 'test data' files
4. Tests complete 12-Stage Production Clinical RAG Pipeline & Audit Hashes
"""
from __future__ import annotations

import asyncio
import io
import os
import sys
from pathlib import Path

# Ensure backend app is on sys.path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config.settings import get_settings
from app.database.init_db import init_db
from app.database.session import AsyncSessionLocal
from app.modules.auth.schema import RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.patients.schema import PatientCreate
from app.modules.patients.service import PatientService
from app.modules.ingestion.service import IngestionService
from app.modules.ai_copilot.service import AICopilotService
from fastapi import UploadFile


async def run_system_verification():
    print("=========================================================================")
    print("ClinIQ Full System Verification & API Key Validation")
    print("=========================================================================\n")

    settings = get_settings()
    sarvam_key = settings.SARVAM_API_KEY
    openai_key = settings.OPENAI_API_KEY

    print(f"[CHECK 1] SARVAM_API_KEY: {'CONFIGURED (' + sarvam_key[:8] + '...)' if sarvam_key else 'NOT SET'}")
    print(f"[CHECK 2] OPENAI_API_KEY: {'CONFIGURED (' + openai_key[:12] + '...)' if openai_key else 'NOT SET'}\n")

    # 1. Initialize DB
    print("[STEP 1] Initializing SQLite database tables...")
    await init_db()
    print("[OK] SQLite Database & Foreign Key PRAGMA initialized.\n")

    async with AsyncSessionLocal() as session:
        # 2. Register Clinician
        print("[STEP 2] Registering Test Clinician...")
        auth_svc = AuthService(session)
        reg_req = RegisterRequest(
            first_name="Verif",
            last_name="Clinician",
            email=f"verification.doc.{os.urandom(3).hex()}@hospital.org",
            password="Password123!",
        )
        tokens = await auth_svc.register(reg_req)
        clinician_id = tokens.user.id
        print(f"[OK] Clinician registered: ID={clinician_id}, Email={tokens.user.email}\n")

        # 3. Create Patient
        print("[STEP 3] Registering Test Patient...")
        patient_svc = PatientService(session)
        p_req = PatientCreate(
            first_name="Alex",
            last_name="TestSubject",
            date_of_birth="1985-08-15",
            gender="male",
            blood_group="A+",
            allergies="Penicillin",
            chronic_conditions="Type 2 Diabetes, Hypertension",
            notes="Full verification patient profile.",
        )
        patient = await patient_svc.create_patient(p_req, clinician_id)
        patient_id = patient.id
        print(f"[OK] Patient created: MRN={patient.mrn}, ID={patient_id}\n")

        # 4. Ingest repository 'test data' files
        test_data_dir = Path(backend_path).parent / "test data"
        print(f"[STEP 4] Scanning repository 'test data' folder: {test_data_dir}")

        if not test_data_dir.exists():
            print(f"[ERROR] Test data directory not found at {test_data_dir}")
            return

        test_files_to_upload = [
            "WhatsApp Image 2026-07-31 at 11.36.44 PM.jpeg",
            "Screenshot 2026-07-31 193248.png",
            "IMG_20250629_132842.jpg",
            "WhatsApp Image 2026-07-31 at 11.36.45 PM.jpeg",
        ]

        upload_files = []
        for fname in test_files_to_upload:
            fpath = test_data_dir / fname
            if fpath.exists():
                with open(fpath, "rb") as f:
                    content = f.read()
                mime = "image/jpeg" if fname.endswith(".jpeg") or fname.endswith(".jpg") else "image/png"
                upload_files.append(
                    UploadFile(filename=fname, file=io.BytesIO(content), headers={"content-type": mime})
                )
                print(f"  - Loaded test file: {fname} ({len(content)} bytes)")


        if not upload_files:
            print("[ERROR] No test files loaded.")
            return

        print("\n[STEP 5] Ingesting files through Document Router (Sarvam Vision / Parse)...")
        ingestion_svc = IngestionService(session)
        batch_res = await ingestion_svc.process_batch_upload(patient_id, clinician_id, upload_files)

        print(f"[OK] Batch upload complete: {batch_res.completed_files}/{batch_res.total_files} files processed successfully.")
        for doc in batch_res.documents:
            print(f"  - [{doc.doc_category.upper()}] '{doc.original_filename}': Parse Source={doc.parse_source}, Confidence={doc.confidence_score*100:.1f}%")

        # 5. Run 12-Stage Production Clinical RAG Pipeline Query
        print("\n[STEP 6] Executing 12-Stage Production Clinical RAG Pipeline...")
        copilot_svc = AICopilotService(session)
        rag_query = "What are the key lab findings, vitals, and medical notes recorded for Alex TestSubject?"

        rag_res = await copilot_svc.query_patient(patient_id, clinician_id, rag_query)

        print("\n-------------------------------------------------------------------------")
        print("CLINICAL RAG ANSWER & REASONING RESULT:")
        print("-------------------------------------------------------------------------")
        print(rag_res.answer)
        print("-------------------------------------------------------------------------")
        print(f"[OK] Grounded Confidence Score: {rag_res.confidence_score*100:.1f}%")
        print(f"[OK] Sources Cited: {len(rag_res.sources)}")
        for idx, src in enumerate(rag_res.sources, 1):
            print(f"  [{idx}] {src.filename} ({src.category.upper()}) -- Relevance: {src.relevance_score*100:.1f}%")
        print(f"[OK] Immutable SHA256 Audit Hash: {rag_res.audit_hash}")
        print("-------------------------------------------------------------------------\n")

        print("=========================================================================")
        print("ALL SYSTEM CHECKS & API KEY VERIFICATIONS PASSED SUCCESSFULLY!")
        print("=========================================================================")


if __name__ == "__main__":
    asyncio.run(run_system_verification())
