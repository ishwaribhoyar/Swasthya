"""
Clinical Service.
Controls clinical analysis, lab extraction, 8-organ system scoring, and alert generation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
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
        Run clinical intelligence analysis over all ingested documents for patient.
        """
        docs = await self._ingestion_repo.list_documents_for_patient(patient_id, clinician_id, status="completed")
        combined_text = "\n\n".join(d.extracted_text or "" for d in docs)

        # 1. Parse Labs
        parsed_labs = MedicalParser.parse_labs(combined_text)
        lab_entities: List[LabResult] = []
        for pl in parsed_labs:
            lab_entities.append(
                LabResult(
                    patient_id=patient_id,
                    clinician_id=clinician_id,
                    test_name=pl["test_name"],
                    test_code=pl["test_code"],
                    numeric_value=pl["numeric_value"],
                    unit=pl["unit"],
                    ref_min=pl["ref_min"],
                    ref_max=pl["ref_max"],
                    status=pl["status"],
                    confidence_score=pl["confidence_score"],
                )
            )
        if lab_entities:
            await self._repo.save_lab_results(lab_entities)

        # 2. Parse Vitals
        parsed_vitals = MedicalParser.parse_vitals(combined_text)
        vital_entity: Optional[VitalSign] = None
        if parsed_vitals and any(k in parsed_vitals for k in ["sbp", "spo2", "heart_rate"]):
            vital_entity = VitalSign(
                patient_id=patient_id,
                clinician_id=clinician_id,
                sbp=parsed_vitals.get("sbp"),
                dbp=parsed_vitals.get("dbp"),
                heart_rate=parsed_vitals.get("heart_rate"),
                spo2=parsed_vitals.get("spo2"),
                respiratory_rate=parsed_vitals.get("respiratory_rate"),
                temperature_c=parsed_vitals.get("temperature_c"),
                bmi=parsed_vitals.get("bmi"),
                status=parsed_vitals.get("status", "NORMAL"),
            )
            await self._repo.save_vital_sign(vital_entity)

        # 3. Calculate 8-Organ Scores
        organ_data = OrganScoringEngine.calculate_scores(parsed_labs, parsed_vitals)
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

        # 4. Generate Clinical Alerts
        alert_data = AlertEngine.generate_alerts(parsed_labs, parsed_vitals)
        alert_entities: List[ClinicalAlert] = [
            ClinicalAlert(
                patient_id=patient_id,
                clinician_id=clinician_id,
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
            labs_count=len(lab_entities),
            alerts_count=len(alert_entities),
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
