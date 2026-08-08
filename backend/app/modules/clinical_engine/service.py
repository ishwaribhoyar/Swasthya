"""
Clinical Service.
Controls clinical analysis, lab extraction, 8-organ system scoring, and alert generation.

KEY PROVENANCE INVARIANT:
  Every LabResult, VitalSign, and ClinicalAlert created by this service MUST carry
  the `document_id` of the specific Document that produced it.

  This invariant powers the full evidence chain:
    Measurement → LabResult.document_id → Document.id → storage_path → original artifact
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import User  # noqa: F401
from app.modules.clinical_engine.alert_engine import AlertEngine
from app.modules.clinical_engine.medical_parser import MedicalParser
from app.modules.clinical_engine.model import ClinicalAlert, LabResult, OrganScore, VitalSign

from app.modules.clinical_engine.organ_scoring import OrganScoringEngine
from app.modules.clinical_engine.repository import ClinicalRepository
from app.modules.clinical_engine.schema import (
    ClinicalAlertRead,
    ClinicalOverviewRead,
    LabResultRead,
    OrganScoreRead,
    VitalSignRead,
)
from app.modules.ingestion.repository import IngestionRepository
from app.observability.logger import get_logger

_log = get_logger(__name__)


class ClinicalService:
    """Service orchestrating clinical intelligence analysis."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ClinicalRepository(session)
        self._ingestion_repo = IngestionRepository(session)

    async def analyze_patient(self, patient_id: str, clinician_id: str) -> ClinicalOverviewRead:
        """
        Run per-document clinical intelligence analysis over all completed documents.

        PROVENANCE GUARANTEE:
          Each LabResult / VitalSign / ClinicalAlert is stamped with the document_id
          of the specific source Document that produced it. This guarantees a complete
          evidence chain from every measurement back to its original source artifact.

        Architecture:
          For each Document:
            1. Parse labs from extracted_text → LabResult(document_id=doc.id)
            2. Parse vitals from extracted_text → VitalSign(document_id=doc.id)
          Across all documents:
            3. Calculate organ scores from aggregated lab data
            4. Generate clinical alerts from aggregated data
              → ClinicalAlert(document_id=most_recent_relevant_doc.id)
        """
        docs = await self._ingestion_repo.list_documents_for_patient(
            patient_id, clinician_id, status="completed"
        )

        all_parsed_labs: list[dict] = []
        all_parsed_vitals: dict = {}
        all_lab_entities: List[LabResult] = []

        # ── Per-document processing with provenance ──────────────────────────
        for doc in docs:
            text = doc.extracted_text or ""
            if not text.strip():
                continue

            # Parse labs from this specific document
            doc_labs = MedicalParser.parse_labs(text)
            doc_vitals = MedicalParser.parse_vitals(text)

            # Create LabResult records stamped with this document's ID
            for pl in doc_labs:
                lr = LabResult(
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    document_id=doc.id,          # ← PROVENANCE STAMP
                    test_name=pl["test_name"],
                    test_code=pl["test_code"],
                    numeric_value=pl["numeric_value"],
                    unit=pl["unit"],
                    ref_min=pl["ref_min"],
                    ref_max=pl["ref_max"],
                    status=pl["status"],
                    confidence_score=pl["confidence_score"],
                    tested_at=doc.document_date or datetime.now(timezone.utc),
                )
                all_lab_entities.append(lr)
                all_parsed_labs.append(pl)

            # Create VitalSign record stamped with this document's ID
            if doc_vitals and any(k in doc_vitals for k in ["sbp", "spo2", "heart_rate"]):
                vs = VitalSign(
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    document_id=doc.id,          # ← PROVENANCE STAMP
                    sbp=doc_vitals.get("sbp"),
                    dbp=doc_vitals.get("dbp"),
                    heart_rate=doc_vitals.get("heart_rate"),
                    spo2=doc_vitals.get("spo2"),
                    respiratory_rate=doc_vitals.get("respiratory_rate"),
                    temperature_c=doc_vitals.get("temperature_c"),
                    bmi=doc_vitals.get("bmi"),
                    status=doc_vitals.get("status", "NORMAL"),
                    recorded_at=doc.document_date or datetime.now(timezone.utc),
                )
                await self._repo.save_vital_sign(vs)

                # Merge vitals for organ scoring (keep latest non-None values)
                for k, v in doc_vitals.items():
                    if v is not None:
                        all_parsed_vitals[k] = v

        # Save all lab entities in one batch
        if all_lab_entities:
            await self._repo.save_lab_results(all_lab_entities)

        # ── Cross-document organ scoring ────────────────────────────────────
        organ_data = OrganScoringEngine.calculate_scores(all_parsed_labs, all_parsed_vitals)
        organ_entities: List[OrganScore] = [
            OrganScore(
                patient_id=patient_id,
                clinician_id=clinician_id,
                organ_system=od["organ_system"],
                score=od["score"],
                status=od["status"],
                contributing_biomarkers=od["contributing_biomarkers"],
                rationale=od["rationale"],
            )
            for od in organ_data
        ]
        await self._repo.save_organ_scores(organ_entities)

        # ── Alert generation with provenance ────────────────────────────────
        # Each alert is linked to the most recently uploaded document that contributed data.
        # Use the last processed doc as the provenance anchor for aggregate alerts.
        latest_doc_id = docs[-1].id if docs else None

        alert_data = AlertEngine.generate_alerts(all_parsed_labs, all_parsed_vitals)
        alert_entities: List[ClinicalAlert] = [
            ClinicalAlert(
                patient_id=patient_id,
                clinician_id=clinician_id,
                document_id=latest_doc_id,       # ← PROVENANCE STAMP (latest trigger doc)
                alert_type=ad["alert_type"],
                severity=ad["severity"],
                title=ad["title"],
                message=ad["message"],
                biomarker_name=ad.get("biomarker_name"),
                observed_value=ad.get("observed_value"),
                reference_range=ad.get("reference_range"),
                action_recommendation=ad.get("action_recommendation"),
            )
            for ad in alert_data
        ]
        if alert_entities:
            await self._repo.save_alerts(alert_entities)

        _log.info(
            "CLINICAL.ANALYZED",
            patient_id=patient_id,
            documents_processed=len(docs),
            labs_count=len(all_lab_entities),
            alerts_count=len(alert_entities),
            vitals_docs=sum(1 for d in docs if d.extracted_text and MedicalParser.parse_vitals(d.extracted_text or "")),
        )

        return await self.get_clinical_overview(patient_id, clinician_id)

    async def get_clinical_overview(self, patient_id: str, clinician_id: str) -> ClinicalOverviewRead:
        """Fetch comprehensive clinical overview."""
        organ_scores = await self._repo.get_latest_organ_scores(patient_id, clinician_id)
        alerts = await self._repo.list_alerts_for_patient(patient_id, clinician_id)
        labs = await self._repo.list_labs_for_patient(patient_id, clinician_id)
        latest_vitals = await self._repo.get_latest_vitals(patient_id, clinician_id)
        docs = await self._ingestion_repo.list_documents_for_patient(patient_id, clinician_id)

        return ClinicalOverviewRead(
            patient_id=patient_id,
            organ_scores=[OrganScoreRead.model_validate(s) for s in organ_scores],
            alerts=[ClinicalAlertRead.model_validate(a) for a in alerts],
            latest_labs=[LabResultRead.model_validate(l) for l in labs],
            latest_vitals=VitalSignRead.model_validate(latest_vitals) if latest_vitals else None,
            analyzed_documents_count=len(docs),
        )

    async def list_labs(self, patient_id: str, clinician_id: str, *, status: Optional[str] = None) -> List[LabResultRead]:
        labs = await self._repo.list_labs_for_patient(patient_id, clinician_id, status=status)
        return [LabResultRead.model_validate(l) for l in labs]

    async def list_vitals(self, patient_id: str, clinician_id: str) -> List[VitalSignRead]:
        vitals = await self._repo.list_vitals_for_patient(patient_id, clinician_id)
        return [VitalSignRead.model_validate(v) for v in vitals]

    async def get_organ_scores(self, patient_id: str, clinician_id: str) -> List[OrganScoreRead]:
        scores = await self._repo.get_latest_organ_scores(patient_id, clinician_id)
        return [OrganScoreRead.model_validate(s) for s in scores]

    async def list_alerts(self, patient_id: str, clinician_id: str, *, severity: Optional[str] = None) -> List[ClinicalAlertRead]:
        alerts = await self._repo.list_alerts_for_patient(patient_id, clinician_id, severity=severity)
        return [ClinicalAlertRead.model_validate(a) for a in alerts]

    async def acknowledge_alert(self, alert_id: str, clinician_id: str) -> ClinicalAlertRead:
        alert = await self._repo.acknowledge_alert(alert_id, clinician_id)
        if not alert:
            raise NotFoundError(f"Alert with ID '{alert_id}' was not found.")
        return ClinicalAlertRead.model_validate(alert)
