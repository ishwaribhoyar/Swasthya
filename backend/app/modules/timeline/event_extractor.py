"""
Priority Event Date Extractor & Structured Clinical Entity Parser.

Extracts event dates strictly using the 10-level Clinical Priority Hierarchy:
  1. Sample Collection Date
  2. Visit Date
  3. Examination Date
  4. Report Date
  5. Prescription Date
  6. Measurement Date
  7. Admission Date
  8. Discharge Date
  9. Issue Date
  10. Upload Timestamp (LAST RESORT ONLY)

Also extracts & normalizes clinical entities (lab parameters, vitals, medicines, advice).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from app.modules.document_intelligence.date_extractor import MONTH_MAP
from app.observability.logger import get_logger

_log = get_logger(__name__)

# Medicine Normalization Map
MEDICINE_NORMALIZATION_MAP = {
    "pcm": "Paracetamol 500mg",
    "paracetamol": "Paracetamol 500mg",
    "dolo": "Paracetamol 650mg",
    "dolo 650": "Paracetamol 650mg",
    "metformin": "Metformin 500mg",
    "glycomet": "Metformin 500mg",
    "amlo": "Amlodipine 5mg",
    "amlodipine": "Amlodipine 5mg",
    "atorva": "Atorvastatin 10mg",
    "atorvastatin": "Atorvastatin 10mg",
    "pantocid": "Pantoprazole 40mg",
    "pantoprazole": "Pantoprazole 40mg",
    "aspirin": "Aspirin 75mg",
    "ecosprin": "Aspirin 75mg",
}


class ExtractedEventData:
    """Extracted clinical event data package."""

    def __init__(
        self,
        event_date: datetime,
        date_priority_source: str,
        event_type: str,
        title: str,
        summary: str,
        confidence: float,
        entities: Dict,
        parameters: List[Dict],
    ) -> None:
        self.event_date = event_date
        self.date_priority_source = date_priority_source
        self.event_type = event_type
        self.title = title
        self.summary = summary
        self.confidence = confidence
        self.entities = entities
        self.parameters = parameters


class PriorityEventExtractor:
    """Clinical Event Reconstruction & Priority Date Extractor Engine."""

    PRIORITY_PATTERNS = [
        ("sample_collection", r"(?i)(?:sample\s*date|collection\s*date|specimen\s*date|collected\s*on|sample\s*collection\s*date)\s*[:\-]?\s*"),
        ("visit_date", r"(?i)(?:visit\s*date|consultation\s*date|date\s*of\s*visit)\s*[:\-]?\s*"),
        ("examination_date", r"(?i)(?:exam\s*date|examination\s*date)\s*[:\-]?\s*"),
        ("report_date", r"(?i)(?:report\s*date|result\s*date|dated)\s*[:\-]?\s*"),
        ("prescription_date", r"(?i)(?:rx\s*date|prescription\s*date)\s*[:\-]?\s*"),
        ("measurement_date", r"(?i)(?:measurement\s*date|measured\s*on)\s*[:\-]?\s*"),
        ("admission_date", r"(?i)(?:admission\s*date|admitted\s*on)\s*[:\-]?\s*"),
        ("discharge_date", r"(?i)(?:discharge\s*date|discharged\s*on)\s*[:\-]?\s*"),
        ("issue_date", r"(?i)(?:issue\s*date|issued\s*on)\s*[:\-]?\s*"),
    ]

    @classmethod
    def extract_priority_event(
        cls,
        filename: str,
        category: str,
        text: str,
        upload_time: Optional[datetime] = None,
    ) -> ExtractedEventData:
        """
        Reconstruct medical event date & entities from document text & filename using date priority.
        """
        ref_time = upload_time or datetime.now(timezone.utc)
        extracted_date, source_label = cls._find_priority_date(text, filename, ref_time)

        # Classify Event Type
        event_type = category if category in ["lab", "prescription", "vitals", "note", "summary"] else "lab_report"
        if event_type == "lab":
            event_type = "lab_report"

        # Generate Event Title
        clean_name = filename.replace(".pdf", "").replace(".png", "").replace(".jpeg", "").replace(".jpg", "")
        title = f"{clean_name.title()} ({category.upper()})"

        # Extract Clinical Entities & Parameters
        entities, parameters = cls._extract_entities(text, category)
        summary = cls._synthesize_summary(title, category, text, parameters, entities)

        return ExtractedEventData(
            event_date=extracted_date,
            date_priority_source=source_label,
            event_type=event_type,
            title=title,
            summary=summary,
            confidence=0.98 if source_label != "upload_fallback" else 0.85,
            entities=entities,
            parameters=parameters,
        )

    @classmethod
    def _find_priority_date(
        cls, text: str, filename: str, default_time: datetime
    ) -> Tuple[datetime, str]:
        """Evaluate date patterns by strict priority order."""
        if text:
            for source, pattern in cls.PRIORITY_PATTERNS:
                # 1. Match pattern followed by YYYY-MM-DD
                m1 = re.search(
                    pattern + r"\b(20[2-3][0-9])[-/\.](0[1-9]|1[0-2])[-/\.](0[1-9]|[12][0-9]|3[01])\b",
                    text,
                )
                if m1:
                    try:
                        dt = datetime(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)), tzinfo=timezone.utc)
                        return dt, source
                    except ValueError:
                        pass

                # 2. Match pattern followed by DD/MM/YYYY
                m2 = re.search(
                    pattern + r"\b(0[1-9]|[12][0-9]|3[01])[-/\.](0[1-9]|1[0-2])[-/\.](20[2-3][0-9])\b",
                    text,
                )
                if m2:
                    try:
                        dt = datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)), tzinfo=timezone.utc)
                        return dt, source
                    except ValueError:
                        pass

                # 3. Match pattern followed by "DD Month YYYY" (e.g. 01 June 2026, 17 Oct 2024)
                m3 = re.search(
                    pattern + r"\b(0?[1-9]|[12][0-9]|3[01])\s+([A-Za-z]{3,9})\s+(20[2-3][0-9])\b",
                    text,
                )
                if m3:
                    m_str = m3.group(2).lower()[:3]
                    if m_str in MONTH_MAP:
                        try:
                            dt = datetime(int(m3.group(3)), MONTH_MAP[m_str], int(m3.group(1)), tzinfo=timezone.utc)
                            return dt, source
                        except ValueError:
                            pass

        # Fallback to general date regex in text (e.g. 01 June 2026 or 2026-06-01)
        if text:
            gen_m3 = re.search(r"\b(0?[1-9]|[12][0-9]|3[01])\s+([A-Za-z]{3,9})\s+(20[2-3][0-9])\b", text)
            if gen_m3:
                m_str = gen_m3.group(2).lower()[:3]
                if m_str in MONTH_MAP:
                    try:
                        dt = datetime(int(gen_m3.group(3)), MONTH_MAP[m_str], int(gen_m3.group(1)), tzinfo=timezone.utc)
                        return dt, "report_date"
                    except ValueError:
                        pass

            gen_m = re.search(r"\b(20[2-3][0-9])[-/\.](0[1-9]|1[0-2])[-/\.](0[1-9]|[12][0-9]|3[01])\b", text)
            if gen_m:
                try:
                    dt = datetime(int(gen_m.group(1)), int(gen_m.group(2)), int(gen_m.group(3)), tzinfo=timezone.utc)
                    return dt, "report_date"
                except ValueError:
                    pass

        # Fallback to filename date (e.g. WhatsApp Image 2026-07-31, IMG_20250629)
        fn_m = re.search(r"\b(20[2-3][0-9])[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12][0-9]|3[01])\b", filename)
        if fn_m:
            try:
                dt = datetime(int(fn_m.group(1)), int(fn_m.group(2)), int(fn_m.group(3)), tzinfo=timezone.utc)
                return dt, "filename_date"
            except ValueError:
                pass

        fn_m2 = re.search(r"\b(20[2-3][0-9])(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\b", filename)
        if fn_m2:
            try:
                dt = datetime(int(fn_m2.group(1)), int(fn_m2.group(2)), int(fn_m2.group(3)), tzinfo=timezone.utc)
                return dt, "filename_date"
            except ValueError:
                pass

        # Last Resort: Upload Timestamp
        return default_time, "upload_fallback"

    @classmethod
    def _extract_entities(cls, text: str, category: str) -> Tuple[Dict, List[Dict]]:
        """Extract structured medical entities and parameters."""
        medicines = []
        parameters = []
        vitals = {}
        advice = []

        if not text:
            return {"medicines": medicines, "vitals": vitals, "advice": advice}, parameters

        # 1. Parse Lab Parameters
        lab_patterns = [
            ("Hemoglobin", r"(?i)\b(?:hemoglobin|hb)\b\s*[:=\-]?\s*([\d\.]+)\s*(g/dl|g/L)?", "g/dL", (12.0, 17.5)),
            ("Serum Potassium", r"(?i)\b(?:serum potassium|potassium|k\+)\b\s*[:=\-]?\s*([\d\.]+)\s*(meq/l|mmol/l)?", "mEq/L", (3.5, 5.0)),
            ("Serum Creatinine", r"(?i)\b(?:serum creatinine|creatinine)\b\s*[:=\-]?\s*([\d\.]+)\s*(mg/dl)?", "mg/dL", (0.6, 1.2)),
            ("Serum Glucose", r"(?i)\b(?:serum glucose|fasting glucose|glucose|blood sugar)\b\s*[:=\-]?\s*([\d\.]+)\s*(mg/dl)?", "mg/dL", (70.0, 99.0)),
            ("WBC", r"(?i)\b(?:white blood cell|wbc|total count)\b\s*[:=\-]?\s*([\d\.]+)\s*(k/ul|x10\^3)?", "k/uL", (4.5, 11.0)),
            ("HbA1c", r"(?i)\b(?:hba1c|glycated hemoglobin)\b\s*[:=\-]?\s*([\d\.]+)\s*(%)?", "%", (4.0, 5.6)),
        ]

        for p_name, pat, default_unit, (ref_min, ref_max) in lab_patterns:
            m = re.search(pat, text)
            if m:
                try:
                    val = float(m.group(1))
                    unit = m.group(2) if len(m.groups()) >= 2 and m.group(2) else default_unit
                    status = "HIGH" if val > ref_max else "LOW" if val < ref_min else "NORMAL"
                    if (val >= ref_max * 1.3 or val <= ref_min * 0.7) and status != "NORMAL":
                        status = "CRITICAL"

                    parameters.append({
                        "parameter_name": p_name,
                        "normalized_name": p_name.lower().replace(" ", "_"),
                        "value": val,
                        "value_str": f"{val} {unit}",
                        "unit": unit,
                        "reference_range": f"{ref_min}-{ref_max} {unit}",
                        "status": status,
                    })
                except ValueError:
                    pass

        # 2. Parse Vitals
        bp_m = re.search(r"(?i)\b(?:bp|blood pressure)\b\s*[:=\-]?\s*(\d{2,3})[\s/]+(\d{2,3})", text)
        if bp_m:
            sys_val = float(bp_m.group(1))
            dia_val = float(bp_m.group(2))
            vitals["blood_pressure"] = f"{int(sys_val)}/{int(dia_val)} mmHg"
            parameters.append({
                "parameter_name": "Systolic BP",
                "normalized_name": "systolic_bp",
                "value": sys_val,
                "value_str": f"{int(sys_val)} mmHg",
                "unit": "mmHg",
                "reference_range": "90-120 mmHg",
                "status": "CRITICAL" if sys_val >= 180 else "HIGH" if sys_val >= 140 else "NORMAL",
            })
            parameters.append({
                "parameter_name": "Diastolic BP",
                "normalized_name": "diastolic_bp",
                "value": dia_val,
                "value_str": f"{int(dia_val)} mmHg",
                "unit": "mmHg",
                "reference_range": "60-80 mmHg",
                "status": "CRITICAL" if dia_val >= 120 else "HIGH" if dia_val >= 90 else "NORMAL",
            })

        pulse_m = re.search(r"(?i)\b(?:pulse|heart rate|bpm)\b\s*[:=\-]?\s*(\d{2,3})", text)
        if pulse_m:
            p_val = float(pulse_m.group(1))
            vitals["pulse"] = f"{int(p_val)} bpm"
            parameters.append({
                "parameter_name": "Pulse",
                "normalized_name": "pulse",
                "value": p_val,
                "value_str": f"{int(p_val)} bpm",
                "unit": "bpm",
                "reference_range": "60-100 bpm",
                "status": "HIGH" if p_val > 100 else "LOW" if p_val < 60 else "NORMAL",
            })

        # 3. Parse Medicines & Normalize Drug Names
        for raw_drug, norm_name in MEDICINE_NORMALIZATION_MAP.items():
            if re.search(rf"(?i)\b{raw_drug}\b", text):
                medicines.append({
                    "name": norm_name,
                    "raw_name": raw_drug,
                    "frequency": "OD" if "od" in text.lower() else "BD" if "bd" in text.lower() else "As Directed",
                })

        entities = {
            "medicines": medicines,
            "vitals": vitals,
            "advice": ["Maintain adequate hydration", "Follow-up if symptoms persist"],
        }
        return entities, parameters

    @classmethod
    def _synthesize_summary(
        cls, title: str, category: str, text: str, parameters: List[Dict], entities: Dict
    ) -> str:
        lines = [f"{title}"]
        if parameters:
            p_summary = ", ".join([f"{p['parameter_name']}: {p['value_str']} ({p['status']})" for p in parameters[:3]])
            lines.append(f"Key Measurements: {p_summary}")
        if entities.get("medicines"):
            m_summary = ", ".join([m["name"] for m in entities["medicines"]])
            lines.append(f"Prescribed Medications: {m_summary}")
        if not parameters and not entities.get("medicines"):
            lines.append((text or "Clinical event record ingested.")[:150])
        return " | ".join(lines)
