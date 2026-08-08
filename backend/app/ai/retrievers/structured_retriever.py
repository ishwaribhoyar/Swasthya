"""
Structured Clinical Data Retriever for ClinIQ Phase 5 RAG.

Queries SQLite-backed structured records:
- Parameter History & Trends (Phase 4 deterministic analytics)
- Medicine History & Prescription Counts
- Timeline Events & Visit Groups
- Vitals Records
- 8-Organ System Scores
- Active Clinical Severity Alerts

Bypasses vector RAG path for deterministic queries.
Strictly scoped by patient_id and clinician_id (JWT.sub).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient
from app.modules.clinical_engine.model import ClinicalAlert, OrganScore
from app.modules.clinical_engine.service import ClinicalService
from app.modules.timeline.service import TimelineService
from app.modules.analytics.service import AnalyticsService
from app.observability.logger import get_logger

_log = get_logger(__name__)


class StructuredEvidence:
    """Container for retrieved structured clinical evidence."""

    def __init__(
        self,
        query_type: str,
        patient_id: str,
        evidence_summary: str,
        raw_data: Dict[str, Any],
        source_records: List[Dict[str, Any]],
        confidence_level: str = "HIGH",
    ) -> None:
        self.query_type = query_type
        self.patient_id = patient_id
        self.evidence_summary = evidence_summary
        self.raw_data = raw_data
        self.source_records = source_records
        self.confidence_level = confidence_level


class StructuredRetriever:
    """Queries structured SQLite tables and Phase 4 deterministic clinical engines."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._clinical_service = ClinicalService(session)
        self._timeline_service = TimelineService(session)
        self._analytics_service = AnalyticsService(session)

    async def retrieve_patient_summary(
        self, patient_id: str, clinician_id: str
    ) -> StructuredEvidence:
        """Fetch full patient clinical overview (demographics, labs, organ scores, active alerts)."""
        overview = await self._clinical_service.analyze_patient(patient_id, clinician_id)
        
        # Deduplicate latest_labs by test_name
        unique_labs: Dict[str, Any] = {}
        for lab in overview.latest_labs:
            if lab.test_name not in unique_labs:
                unique_labs[lab.test_name] = lab
        deduped_labs = list(unique_labs.values())

        sources = []
        for lab in deduped_labs:
            sources.append({
                "record_id": lab.id,
                "title": f"Lab Result: {lab.test_name}",
                "event_date": lab.tested_at.strftime("%Y-%m-%d") if lab.tested_at else "Recent",
                "document_type": "LAB",
            })

        for alt in overview.alerts:
            sources.append({
                "record_id": alt.id,
                "title": f"Alert: {alt.title}",
                "event_date": "Active",
                "document_type": "ALERT",
            })

        labs_str = "\n".join([
            f"  - {l.test_name}: {l.numeric_value} {l.unit} (Status: {l.status})"
            for l in deduped_labs
        ]) if deduped_labs else "  - None documented"

        alerts_str = "\n".join([
            f"  - [{a.severity}] {a.title}: {a.message}"
            for a in overview.alerts
        ]) if overview.alerts else "  - None"

        organ_str = "\n".join([
            f"  - {s.organ_system.title()}: {f'{s.score}% ({s.status})' if s.score is not None else 'Insufficient Data'}"
            for s in overview.organ_scores
        ])

        summary_text = (
            f"PATIENT CLINICAL SUMMARY:\n"
            f"- Total Lab Biomarkers Tracked: {len(deduped_labs)}\n\n"
            f"- Active Clinical Alerts ({len(overview.alerts)}):\n{alerts_str}\n\n"
            f"- 8-Organ System Health Scores:\n{organ_str}\n\n"
            f"- Unique Lab Biomarkers:\n{labs_str}"
        )

        return StructuredEvidence(
            query_type="PATIENT_SUMMARY",
            patient_id=patient_id,
            evidence_summary=summary_text,
            raw_data={
                "organ_scores": [s.model_dump() for s in overview.organ_scores],
                "alerts": [a.model_dump() for a in overview.alerts],
                "latest_labs": [l.model_dump() for l in deduped_labs],
            },
            source_records=sources,
            confidence_level="HIGH" if deduped_labs else "LOW",
        )

    async def retrieve_parameter_trend(
        self, patient_id: str, clinician_id: str, parameter_name: Optional[str] = None
    ) -> StructuredEvidence:
        """Fetch deterministic parameter history & trend analysis from Phase 4 engine."""
        analytics = await self._analytics_service.get_patient_analytics(patient_id, clinician_id)
        
        target_trends = analytics.parameter_trends
        if parameter_name:
            p_lower = parameter_name.lower()
            target_trends = [
                t for t in analytics.parameter_trends
                if p_lower in t.parameter_name.lower() or p_lower in t.normalized_name.lower()
            ]

        if not target_trends:
            return StructuredEvidence(
                query_type="TREND_QUERY",
                patient_id=patient_id,
                evidence_summary=f"No recorded parameter history found matching '{parameter_name or 'all'}'.",
                raw_data={"trends": []},
                source_records=[],
                confidence_level="INSUFFICIENT",
            )

        summary_lines = []
        sources = []
        for tr in target_trends:
            pts_str = " -> ".join([f"{pt.value} {pt.unit} ({pt.date})" for pt in tr.data_points])
            summary_lines.append(
                f"Parameter: {tr.parameter_name} ({tr.unit})\n"
                f"  - Trend Direction: {tr.direction} (Risk: {tr.risk_level})\n"
                f"  - Historical Datapoints: {pts_str}"
            )
            for pt in tr.data_points:
                sources.append({
                    "record_id": f"lab_{tr.normalized_name}_{pt.date}",
                    "title": f"{tr.parameter_name} Measurement",
                    "event_date": pt.date,
                    "document_type": "LAB",
                })

        return StructuredEvidence(
            query_type="TREND_QUERY",
            patient_id=patient_id,
            evidence_summary="\n".join(summary_lines),
            raw_data={"trends": [t.model_dump() for t in target_trends]},
            source_records=sources,
            confidence_level="HIGH" if len(target_trends[0].data_points) >= 2 else "MEDIUM",
        )

    async def retrieve_medicine_history(
        self, patient_id: str, clinician_id: str, drug_name: Optional[str] = None
    ) -> StructuredEvidence:
        """Fetch exact prescription history & frequency count from structured timeline events."""
        visit_groups = await self._timeline_service.get_patient_timeline(patient_id, clinician_id)
        
        prescriptions = []
        sources = []

        for vg in visit_groups:
            for ev in vg.events:
                # Inspect entities_json for parsed medicines
                import json
                try:
                    entities = json.loads(ev.entities_json) if ev.entities_json else {}
                    meds = entities.get("medicines", [])
                    for m in meds:
                        m_name = m.get("name", "")
                        if not drug_name or drug_name.lower() in m_name.lower() or drug_name.lower() in m.get("raw_name", "").lower():
                            prescriptions.append({
                                "medicine_name": m_name,
                                "raw_name": m.get("raw_name", ""),
                                "frequency": m.get("frequency", "As Directed"),
                                "event_date": ev.event_date.strftime("%Y-%m-%d"),
                                "document_title": ev.title,
                            })
                            sources.append({
                                "record_id": ev.id,
                                "title": ev.title,
                                "event_date": ev.event_date.strftime("%Y-%m-%d"),
                                "document_type": "PRESCRIPTION",
                            })
                except Exception:
                    pass

        count = len(prescriptions)
        if count == 0:
            drug_label = f"for '{drug_name}'" if drug_name else ""
            return StructuredEvidence(
                query_type="MEDICINE_QUERY",
                patient_id=patient_id,
                evidence_summary=f"No prescription records found {drug_label} in the patient's documented history.",
                raw_data={"prescriptions": [], "total_count": 0},
                source_records=[],
                confidence_level="HIGH",
            )

        summary_lines = [f"Total Documented Prescriptions: {count}"]
        for p in prescriptions:
            summary_lines.append(f"- {p['medicine_name']} ({p['frequency']}) on {p['event_date']} [{p['document_title']}]")

        return StructuredEvidence(
            query_type="MEDICINE_QUERY",
            patient_id=patient_id,
            evidence_summary="\n".join(summary_lines),
            raw_data={"prescriptions": prescriptions, "total_count": count},
            source_records=sources,
            confidence_level="HIGH",
        )

    async def retrieve_vitals_history(
        self, patient_id: str, clinician_id: str
    ) -> StructuredEvidence:
        """Fetch vitals history (BP, Pulse, SpO2) from Phase 4 analytics."""
        analytics = await self._analytics_service.get_patient_analytics(patient_id, clinician_id)
        
        vital_trends = [
            t for t in analytics.parameter_trends
            if t.normalized_name in ["systolic_bp", "diastolic_bp", "pulse", "spo2", "heart_rate"]
        ]

        if not vital_trends:
            return StructuredEvidence(
                query_type="VITAL_QUERY",
                patient_id=patient_id,
                evidence_summary="No physical vitals measurements found in patient records.",
                raw_data={"vitals": []},
                source_records=[],
                confidence_level="INSUFFICIENT",
            )

        summary_lines = []
        sources = []
        for tr in vital_trends:
            pts_str = ", ".join([f"{pt.value} {pt.unit} ({pt.date})" for pt in tr.data_points])
            summary_lines.append(f"{tr.parameter_name}: {pts_str}")
            for pt in tr.data_points:
                sources.append({
                    "record_id": f"vital_{tr.normalized_name}_{pt.date}",
                    "title": f"{tr.parameter_name} Measurement",
                    "event_date": pt.date,
                    "document_type": "VITALS",
                })

        return StructuredEvidence(
            query_type="VITAL_QUERY",
            patient_id=patient_id,
            evidence_summary="\n".join(summary_lines),
            raw_data={"vitals": [t.model_dump() for t in vital_trends]},
            source_records=sources,
            confidence_level="HIGH",
        )

    async def retrieve_timeline_events(
        self, patient_id: str, clinician_id: str, search: Optional[str] = None
    ) -> StructuredEvidence:
        """Fetch timeline visits & events ordered chronologically."""
        visit_groups = await self._timeline_service.get_patient_timeline(
            patient_id=patient_id, clinician_id=clinician_id, search=search
        )

        if not visit_groups:
            return StructuredEvidence(
                query_type="TIMELINE_QUERY",
                patient_id=patient_id,
                evidence_summary="No timeline events found for this patient.",
                raw_data={"visit_groups": []},
                source_records=[],
                confidence_level="INSUFFICIENT",
            )

        summary_lines = []
        sources = []
        for vg in visit_groups[:5]:
            summary_lines.append(f"Visit Date: {vg.display_date} ({vg.event_count} events)")
            for ev in vg.events:
                summary_lines.append(f"  - [{ev.date_priority_source}] {ev.title}: {ev.summary}")
                sources.append({
                    "record_id": ev.id,
                    "title": ev.title,
                    "event_date": vg.visit_date,
                    "document_type": ev.document_type or "CLINICAL_EVENT",
                })

        return StructuredEvidence(
            query_type="TIMELINE_QUERY",
            patient_id=patient_id,
            evidence_summary="\n".join(summary_lines),
            raw_data={"visit_groups": [vg.model_dump() for vg in visit_groups]},
            source_records=sources,
            confidence_level="HIGH",
        )
