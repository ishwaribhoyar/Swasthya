"""
Timeline Service Engine — builds a true longitudinal clinical timeline.

Data architecture:
- timeline_events: one row per document/encounter (date, type, title)
- lab_results: all extracted lab parameters per document
- parameter_history: all extracted vitals/labs with longitudinal tracking
- These are JOINed to produce rich ClinicalEncounterRead objects
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.timeline.model import TimelineEvent
from app.modules.timeline.schema import (
    ClinicalEncounterRead,
    ClinicalObservation,
    TimelineStatsRead,
    VisitGroupRead,
)
from app.observability.logger import get_logger

_log = get_logger(__name__)

# Which categories map to which doc-type labels
_CATEGORY_MAP = {
    "lab_report": "lab",
    "lab": "lab",
    "prescription": "prescription",
    "vitals": "vitals",
    "note": "note",
    "visit": "visit",
    "summary": "summary",
}

_BINARY_GARBAGE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]")


def _is_garbage(text: str) -> bool:
    """Return True if the text is clearly binary/OCR garbage."""
    if not text:
        return True
    # Contains NULL bytes or common zip/binary headers
    if "\x00" in text or text.startswith("PK"):
        return True
    # High proportion of replacement chars or non-printable bytes
    garbage_count = len(_BINARY_GARBAGE_RE.findall(text))
    return garbage_count > len(text) * 0.05


def _clean_text(raw: str) -> str:
    """Strip binary garbage and truncate to a safe length."""
    if not raw:
        return ""
    cleaned = _BINARY_GARBAGE_RE.sub("", raw)
    # Remove markdown table separator lines
    cleaned = re.sub(r"\|\s*-{3,}[^\n]*", "", cleaned)
    # Collapse multiple pipes
    cleaned = re.sub(r"\|{2,}", "|", cleaned)
    return cleaned.strip()


class TimelineService:
    """Service compiling longitudinal patient clinical timelines."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_patient_timeline(
        self,
        patient_id: str,
        clinician_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[VisitGroupRead]:
        """
        Build a rich longitudinal clinical timeline for a patient.

        Strategy:
        1. Fetch all timeline_events for the patient (ordered by event_date DESC)
        2. For each event, JOIN lab_results on document_id to get extracted parameters
        3. Also JOIN parameter_history on record_id for vitals
        4. Group by calendar date
        5. Surface structured ClinicalObservation objects per encounter
        6. Filter out garbage/failed OCR events from the display
        """
        # Step 1: Load all timeline events
        stmt = (
            select(TimelineEvent)
            .where(
                TimelineEvent.patient_id == patient_id,
                TimelineEvent.clinician_id == clinician_id,
            )
            .order_by(TimelineEvent.event_date.desc())
        )
        if category:
            norm_cat = category.upper()
            if norm_cat == "LAB":
                stmt = stmt.where(TimelineEvent.event_type.in_(["lab_report", "lab", "LAB", "LAB_REPORT"]))
            else:
                stmt = stmt.where(TimelineEvent.event_type.ilike(f"%{category}%"))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                TimelineEvent.title.ilike(pattern)
                | TimelineEvent.summary.ilike(pattern)
                | TimelineEvent.entities_json.ilike(pattern)
            )

        result = await self._session.execute(stmt)
        events = result.scalars().all()

        # Step 2: Load lab_results grouped by document_id
        lab_by_doc = await self._load_lab_results_by_doc(patient_id, clinician_id)

        # Step 3: Load parameter_history grouped by record_id
        param_by_record = await self._load_param_history_by_record(patient_id, clinician_id)

        # Step 4: Build rich encounters
        encounter_list: List[ClinicalEncounterRead] = []
        for ev in events:
            encounter = self._build_encounter(ev, lab_by_doc, param_by_record)
            if encounter is not None:
                encounter_list.append(encounter)

        # Step 5: Group by date
        groups = self._group_by_date(encounter_list)

        _log.info(
            "TIMELINE.LOADED",
            patient_id=patient_id,
            total_events=len(events),
            valid_encounters=len(encounter_list),
            visit_groups=len(groups),
        )
        return groups

    async def get_timeline_stats(
        self, patient_id: str, clinician_id: str
    ) -> TimelineStatsRead:
        """Compute longitudinal statistics for the timeline header."""
        result = await self._session.execute(
            select(TimelineEvent)
            .where(
                TimelineEvent.patient_id == patient_id,
                TimelineEvent.clinician_id == clinician_id,
            )
            .order_by(TimelineEvent.event_date.asc())
        )
        events = result.scalars().all()

        if not events:
            return TimelineStatsRead(
                total_events=0,
                first_record=None,
                latest_record=None,
                lab_count=0,
                vitals_count=0,
                prescription_count=0,
                note_count=0,
            )

        lab_count = sum(1 for e in events if "lab" in (e.event_type or "").lower())
        vitals_count = sum(1 for e in events if "vital" in (e.event_type or "").lower())
        rx_count = sum(1 for e in events if "prescription" in (e.event_type or "").lower())
        note_count = sum(1 for e in events if "note" in (e.event_type or "").lower())

        return TimelineStatsRead(
            total_events=len(events),
            first_record=events[0].event_date.strftime("%d %b %Y") if events else None,
            latest_record=events[-1].event_date.strftime("%d %b %Y") if events else None,
            lab_count=lab_count,
            vitals_count=vitals_count,
            prescription_count=rx_count,
            note_count=note_count,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _load_lab_results_by_doc(
        self, patient_id: str, clinician_id: str
    ) -> Dict[str, List[ClinicalObservation]]:
        """Load all lab_results keyed by document_id."""
        rows = await self._session.execute(
            text(
                """
                SELECT document_id, test_name, numeric_value, unit, ref_min, ref_max,
                       status, confidence_score, tested_at
                FROM lab_results
                WHERE patient_id = :pid AND clinician_id = :cid
                ORDER BY tested_at DESC
                """
            ),
            {"pid": patient_id, "cid": clinician_id},
        )
        by_doc: Dict[str, List[ClinicalObservation]] = defaultdict(list)
        for row in rows:
            doc_id, test_name, value, unit, ref_min, ref_max, status, conf, tested_at = row
            if doc_id:
                ref_range = None
                if ref_min is not None and ref_max is not None:
                    ref_range = f"{ref_min}–{ref_max} {unit or ''}".strip()
                by_doc[doc_id].append(
                    ClinicalObservation(
                        name=test_name,
                        value=value,
                        value_str=f"{value} {unit}".strip() if value is not None else "—",
                        unit=unit or "",
                        status=status or "UNKNOWN",
                        reference_range=ref_range,
                        category="lab",
                    )
                )
        return dict(by_doc)

    async def _load_param_history_by_record(
        self, patient_id: str, clinician_id: str
    ) -> Dict[str, List[ClinicalObservation]]:
        """Load all parameter_history keyed by record_id."""
        rows = await self._session.execute(
            text(
                """
                SELECT record_id, parameter_name, value, value_str, unit,
                       reference_range, status, event_date
                FROM parameter_history
                WHERE patient_id = :pid AND clinician_id = :cid
                ORDER BY event_date DESC
                """
            ),
            {"pid": patient_id, "cid": clinician_id},
        )
        by_record: Dict[str, List[ClinicalObservation]] = defaultdict(list)
        for row in rows:
            record_id, p_name, value, value_str, unit, ref_range, status, _ = row
            if record_id:
                # Determine category from parameter name
                cat = "vitals" if p_name and any(
                    v in p_name.lower() for v in ["bp", "pulse", "temp", "blood pressure", "systolic", "diastolic"]
                ) else "lab"
                by_record[record_id].append(
                    ClinicalObservation(
                        name=p_name,
                        value=value,
                        value_str=value_str or f"{value} {unit}".strip(),
                        unit=unit or "",
                        status=status or "UNKNOWN",
                        reference_range=ref_range,
                        category=cat,
                    )
                )
        return dict(by_record)

    def _build_encounter(
        self,
        ev: TimelineEvent,
        lab_by_doc: Dict[str, List[ClinicalObservation]],
        param_by_record: Dict[str, List[ClinicalObservation]],
    ) -> Optional[ClinicalEncounterRead]:
        """
        Build a ClinicalEncounterRead from a TimelineEvent + lab/param lookups.
        Returns None if the event represents a failed/garbage extraction.
        """
        # Collect observations from all sources
        observations: List[ClinicalObservation] = []

        # Primary: lab_results joined by record_id (record_id == document_id)
        doc_id = ev.record_id
        if doc_id:
            observations.extend(lab_by_doc.get(doc_id, []))
            observations.extend(param_by_record.get(doc_id, []))

        # Secondary: parse entities_json if available and not garbage
        if not observations and ev.entities_json:
            try:
                parsed = json.loads(ev.entities_json)
                raw_params = parsed.get("parameters", []) if isinstance(parsed, dict) else []
                for p in raw_params:
                    observations.append(
                        ClinicalObservation(
                            name=p.get("parameter_name") or p.get("name", "Unknown"),
                            value=p.get("value"),
                            value_str=p.get("value_str") or str(p.get("value", "—")),
                            unit=p.get("unit", ""),
                            status=p.get("status", "UNKNOWN"),
                            reference_range=p.get("reference_range"),
                            category="lab",
                        )
                    )
            except (json.JSONDecodeError, AttributeError):
                pass

        # Check for OCR garbage in summary
        summary_raw = ev.summary or ""
        summary_is_garbage = _is_garbage(summary_raw)

        # If no observations AND garbage summary → flag as processing incomplete
        if not observations and summary_is_garbage:
            return ClinicalEncounterRead(
                id=ev.id,
                event_date=ev.event_date,
                display_date=ev.event_date.strftime("%d %b %Y"),
                event_type=ev.event_type or "lab_report",
                document_type=ev.document_type or "DOCUMENT",
                title=_clean_title(ev.title),
                summary=None,
                processing_incomplete=True,
                processing_reason="OCR extraction did not produce usable clinical observations from this document.",
                date_priority_source=ev.date_priority_source or "upload_fallback",
                confidence=ev.confidence or 0.0,
                observations=[],
                record_id=doc_id,
            )

        # Clean the summary
        clean_summary = _clean_text(summary_raw) if not summary_is_garbage else None

        # Deduplicate observations by parameter name (keep highest-confidence / first)
        seen: set = set()
        deduped: List[ClinicalObservation] = []
        for obs in observations:
            key = obs.name.lower().strip() if obs.name else ""
            if key not in seen:
                seen.add(key)
                deduped.append(obs)

        return ClinicalEncounterRead(
            id=ev.id,
            event_date=ev.event_date,
            display_date=ev.event_date.strftime("%d %b %Y"),
            event_type=ev.event_type or "lab_report",
            document_type=ev.document_type or "DOCUMENT",
            title=_clean_title(ev.title),
            summary=clean_summary,
            processing_incomplete=False,
            processing_reason=None,
            date_priority_source=ev.date_priority_source or "report_date",
            confidence=ev.confidence or 0.98,
            observations=deduped,
            record_id=doc_id,
        )

    def _group_by_date(
        self, encounters: List[ClinicalEncounterRead]
    ) -> List[VisitGroupRead]:
        """Group encounters by calendar date (YYYY-MM-DD) and return sorted groups."""
        groups: Dict[str, List[ClinicalEncounterRead]] = defaultdict(list)
        for enc in encounters:
            date_key = enc.event_date.strftime("%Y-%m-%d") if enc.event_date else "Unknown"
            groups[date_key].append(enc)

        visit_groups = []
        for d_str in sorted(groups.keys(), reverse=True):
            enc_list = groups[d_str]
            # Parse display date
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                disp = dt.strftime("%d %b %Y")
                day_label = dt.strftime("%A, %d %B %Y")
            except ValueError:
                disp = d_str
                day_label = d_str

            cats = list(set(e.event_type for e in enc_list))
            total_obs = sum(len(e.observations) for e in enc_list)
            incomplete_count = sum(1 for e in enc_list if e.processing_incomplete)

            visit_groups.append(
                VisitGroupRead(
                    visit_date=d_str,
                    display_date=disp,
                    day_label=day_label,
                    event_count=len(enc_list),
                    observation_count=total_obs,
                    incomplete_count=incomplete_count,
                    categories=cats,
                    encounters=enc_list,
                )
            )
        return visit_groups


def _clean_title(raw: str) -> str:
    """Clean a raw document filename title into a human-readable one."""
    if not raw:
        return "Clinical Document"
    # Remove file extensions and common WhatsApp/screenshot patterns
    title = raw
    title = re.sub(r"\s*\((?:LAB|JPEG|PNG|PDF|PRESCRIPTION|VITALS)\)\s*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"(?i)(whatsapp image|screenshot)\s+\d{4}-\d{2}-\d{2}\s+at\s+[\d\.\s]+(am|pm)?", "Medical Record", title, flags=re.IGNORECASE)
    title = re.sub(r"\s{2,}", " ", title).strip()
    return title or "Clinical Document"
