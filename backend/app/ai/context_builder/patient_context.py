"""
Patient Context Builder Engine.

Compiles a unified, structured clinical snapshot for a patient including:
  1. Patient Demographics & Profile (MRN, Age, Gender, Blood Group, Allergies, Chronic Conditions)
  2. Full Medical Document History & Timeline
  3. Extracted Lab Panels & Vitals Reports
  4. Active Unacknowledged Clinical Alerts & Risk Scores

This snapshot is provided directly to the Hybrid RAG retriever & GPT Reasoning engine
to ensure 100% patient-grounded clinical context.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document
from app.modules.clinical_engine.model import ClinicalAlert
from app.observability.logger import get_logger

_log = get_logger(__name__)


class PatientContextSnapshot:
    """Structured patient context snapshot package."""

    def __init__(
        self,
        patient_id: str,
        clinician_id: str,
        patient_summary_text: str,
        demographics: Dict,
        documents_summary: List[Dict],
        alerts_summary: List[Dict],
    ) -> None:
        self.patient_id = patient_id
        self.clinician_id = clinician_id
        self.patient_summary_text = patient_summary_text
        self.demographics = demographics
        self.documents_summary = documents_summary
        self.alerts_summary = alerts_summary


class PatientContextBuilder:
    """Assembles comprehensive, grounded patient records from SQLite."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def build_snapshot(self, patient_id: str, clinician_id: str) -> PatientContextSnapshot:
        """
        Build full patient context snapshot from database.
        """
        # 1. Fetch Patient Record
        p_stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinician_id == clinician_id,
        )
        p_res = await self._session.execute(p_stmt)
        patient = p_res.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient with ID '{patient_id}' not found.")

        # Calculate age
        today = datetime.today().date()
        dob = patient.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        demographics = {
            "mrn": patient.mrn,
            "full_name": f"{patient.first_name} {patient.last_name}",
            "age": age,
            "gender": patient.gender,
            "blood_group": patient.blood_group or "Unknown",
            "allergies": patient.allergies or "None Reported",
            "chronic_conditions": patient.chronic_conditions or "None Reported",
            "notes": patient.notes or "None",
        }

        # 2. Fetch Patient Documents
        doc_stmt = (
            select(Document)
            .where(
                Document.patient_id == patient_id,
                Document.clinician_id == clinician_id,
                Document.status == "completed",
            )
            .order_by(Document.created_at.desc())
        )
        doc_res = await self._session.execute(doc_stmt)
        docs = doc_res.scalars().all()

        docs_summary = []
        for d in docs:
            docs_summary.append({
                "doc_id": d.id,
                "filename": d.original_filename,
                "category": d.doc_category,
                "parse_source": d.parse_source,
                "created_at": d.created_at.strftime("%Y-%m-%d %H:%M") if d.created_at else "",
                "snippet": (d.extracted_text or "")[:400],
                "full_text": d.extracted_text or "",
            })

        # 3. Fetch Unacknowledged Clinical Alerts
        alert_stmt = (
            select(ClinicalAlert)
            .where(
                ClinicalAlert.patient_id == patient_id,
                ClinicalAlert.clinician_id == clinician_id,
                ClinicalAlert.is_acknowledged == False,
            )
            .order_by(ClinicalAlert.created_at.desc())
        )
        alert_res = await self._session.execute(alert_stmt)
        alerts = alert_res.scalars().all()

        alerts_summary = []
        for a in alerts:
            alerts_summary.append({
                "alert_id": a.id,
                "metric_name": a.metric_name,
                "measured_value": a.measured_value,
                "reference_range": a.reference_range,
                "severity": a.severity,
                "message": a.alert_message,
            })

        # 4. Synthesize Patient Summary Text Block
        summary_lines = [
            f"=== CLINICAL PATIENT CONTEXT: {demographics['full_name']} (MRN: {demographics['mrn']}) ===",
            f"Demographics: Age {demographics['age']}, Gender {demographics['gender'].title()}, Blood Group: {demographics['blood_group']}",
            f"Known Allergies: {demographics['allergies']}",
            f"Chronic Conditions: {demographics['chronic_conditions']}",
            f"Clinical Profile Notes: {demographics['notes']}",
            "",
            f"=== ACTIVE CLINICAL ALERTS ({len(alerts_summary)}) ===",
        ]

        if alerts_summary:
            for a in alerts_summary:
                summary_lines.append(
                    f"• [{a['severity']}] {a['metric_name']}: {a['measured_value']} (Range: {a['reference_range']}) — {a['message']}"
                )
        else:
            summary_lines.append("• No active critical alerts.")

        summary_lines.extend(["", f"=== MEDICAL DOCUMENTS & RECORDS TIMELINE ({len(docs_summary)}) ==="])
        if docs_summary:
            for d in docs_summary:
                summary_lines.append(f"\n--- Document: {d['filename']} ({d['category'].upper()}, {d['created_at']}) ---")
                summary_lines.append(d["full_text"][:1200])
        else:
            summary_lines.append("• No medical documents uploaded for patient yet.")

        patient_summary_text = "\n".join(summary_lines)

        _log.info(
            "PATIENT_CONTEXT.BUILT",
            patient_id=patient_id,
            doc_count=len(docs_summary),
            alert_count=len(alerts_summary),
        )

        return PatientContextSnapshot(
            patient_id=patient_id,
            clinician_id=clinician_id,
            patient_summary_text=patient_summary_text,
            demographics=demographics,
            documents_summary=docs_summary,
            alerts_summary=alerts_summary,
        )
