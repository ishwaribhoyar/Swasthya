"""
Deterministic LOINC-aligned Medical Lab Result Parser & Vitals Extractor.
Parses raw extracted text/HTML/Markdown tables into validated physiological metrics.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, Any

LAB_CONFIG: Dict[str, Dict[str, Any]] = {
    "Hemoglobin": {
        "code": "718-7",
        "patterns": [r"hemoglobin", r"\bhb\b", r"\bhgb\b"],
        "unit": "g/dL",
        "ref_min": 12.0,
        "ref_max": 17.5,
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "WBC": {
        "code": "6690-2",
        "patterns": [r"white blood cell", r"\bwbc\b", r"leukocyte", r"wbc count"],
        "unit": "k/uL",
        "ref_min": 4.5,
        "ref_max": 11.0,
        "critical_low": 2.0,
        "critical_high": 30.0,
    },
    "Platelets": {
        "code": "777-3",
        "patterns": [r"platelet", r"\bplt\b", r"platelet count"],
        "unit": "k/uL",
        "ref_min": 150.0,
        "ref_max": 450.0,
        "critical_low": 50.0,
        "critical_high": 1000.0,
    },
    "Serum Glucose": {
        "code": "2345-7",
        "patterns": [r"fasting glucose", r"blood glucose", r"serum glucose", r"\bglucose\b", r"sugar"],
        "unit": "mg/dL",
        "ref_min": 70.0,
        "ref_max": 99.0,
        "critical_low": 50.0,
        "critical_high": 300.0,
    },
    "HbA1c": {
        "code": "4548-4",
        "patterns": [r"hba1c", r"glycated hemoglobin", r"hemoglobin a1c"],
        "unit": "%",
        "ref_min": 4.0,
        "ref_max": 5.6,
        "critical_low": 3.0,
        "critical_high": 10.0,
    },
    "Serum Creatinine": {
        "code": "2160-0",
        "patterns": [r"serum creatinine", r"\bcreatinine\b"],
        "unit": "mg/dL",
        "ref_min": 0.6,
        "ref_max": 1.2,
        "critical_low": 0.2,
        "critical_high": 3.0,
    },
    "BUN": {
        "code": "3094-0",
        "patterns": [r"blood urea nitrogen", r"\bbun\b", r"urea nitrogen", r"\burea\b"],
        "unit": "mg/dL",
        "ref_min": 7.0,
        "ref_max": 20.0,
        "critical_low": 3.0,
        "critical_high": 60.0,
    },
    "eGFR": {
        "code": "33914-3",
        "patterns": [r"egfr", r"\bgfr\b", r"estimated gfr"],
        "unit": "mL/min/1.73m²",
        "ref_min": 90.0,
        "ref_max": 140.0,
        "critical_low": 30.0,
        "critical_high": 200.0,
    },
    "Serum Sodium": {
        "code": "2951-2",
        "patterns": [r"serum sodium", r"\bsodium\b", r"\bna\b"],
        "unit": "mEq/L",
        "ref_min": 135.0,
        "ref_max": 145.0,
        "critical_low": 120.0,
        "critical_high": 160.0,
    },
    "Serum Potassium": {
        "code": "2823-3",
        "patterns": [r"serum potassium", r"\bpotassium\b", r"\bk\b"],
        "unit": "mEq/L",
        "ref_min": 3.5,
        "ref_max": 5.0,
        "critical_low": 2.8,
        "critical_high": 6.0,
    },
    "Total Bilirubin": {
        "code": "1975-2",
        "patterns": [r"total bilirubin", r"bilirubin"],
        "unit": "mg/dL",
        "ref_min": 0.1,
        "ref_max": 1.2,
        "critical_low": 0.0,
        "critical_high": 5.0,
    },
    "AST": {
        "code": "1920-8",
        "patterns": [r"\bast\b", r"sgot", r"aspartate aminotransferase"],
        "unit": "U/L",
        "ref_min": 10.0,
        "ref_max": 40.0,
        "critical_low": 0.0,
        "critical_high": 200.0,
    },
    "ALT": {
        "code": "1742-6",
        "patterns": [r"\balt\b", r"sgpt", r"alanine aminotransferase"],
        "unit": "U/L",
        "ref_min": 7.0,
        "ref_max": 56.0,
        "critical_low": 0.0,
        "critical_high": 250.0,
    },
    "TSH": {
        "code": "3016-3",
        "patterns": [r"\btsh\b", r"thyroid stimulating hormone"],
        "unit": "uIU/mL",
        "ref_min": 0.4,
        "ref_max": 4.0,
        "critical_low": 0.05,
        "critical_high": 15.0,
    },
    "CRP": {
        "code": "1988-5",
        "patterns": [r"\bcrp\b", r"c-reactive protein"],
        "unit": "mg/L",
        "ref_min": 0.0,
        "ref_max": 3.0,
        "critical_low": 0.0,
        "critical_high": 50.0,
    },
    "Troponin": {
        "code": "10839-9",
        "patterns": [r"troponin", r"troponin i", r"troponin t"],
        "unit": "ng/mL",
        "ref_min": 0.0,
        "ref_max": 0.04,
        "critical_low": 0.0,
        "critical_high": 0.04,
    },
}


class MedicalParser:
    """Medical lab parser extracting canonical lab parameters and vital signs."""

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalize Unicode subscripts, Greek letters, and micro symbols."""
        if not text:
            return ""
        return (
            text.replace("₂", "2")
            .replace("₁", "1")
            .replace("₃", "3")
            .replace("₄", "4")
            .replace("µ", "u")
            .replace("μ", "u")
        )

    @classmethod
    def parse_labs(cls, text: str) -> List[Dict[str, Any]]:
        """Extract lab test values from raw text, Markdown tables, or HTML."""
        if not text:
            return []

        norm_text = cls.normalize_text(text)
        results: List[Dict[str, Any]] = []
        matched_names: set[str] = set()

        lines = norm_text.splitlines()

        for line in lines:
            clean_line = line.strip("| \t")
            if not clean_line or clean_line.startswith("---") or "Parameter" in clean_line:
                continue

            parts = [p.strip() for p in clean_line.split("|")]
            name_part = ""
            val_part = ""

            if len(parts) >= 2 and parts[0] and parts[1]:
                name_part = parts[0]
                val_part = parts[1]
            else:
                match = re.search(r"([A-Za-z0-9\s\-\/\(\)]+)[:\s=]+([0-9,]+(?:\.[0-9]+)?)", line)
                if match:
                    name_part = match.group(1)
                    val_part = match.group(2)

            if not name_part or not val_part:
                continue

            val_clean = val_part.replace(",", "").strip()
            try:
                val = float(val_clean)
            except ValueError:
                continue

            for name, cfg in LAB_CONFIG.items():
                if name in matched_names:
                    continue

                if any(re.search(pat, name_part, re.IGNORECASE) for pat in cfg["patterns"]):
                    # Auto-normalize /uL values (>1000) for WBC and Platelets into k/uL
                    if name in ("WBC", "Platelets") and val > 1000.0:
                        val = round(val / 1000.0, 1)

                    # Determine status
                    status = "NORMAL"
                    if val < cfg["critical_low"]:
                        status = "CRITICAL_LOW"
                    elif val > cfg["critical_high"]:
                        status = "CRITICAL_HIGH"
                    elif val < cfg["ref_min"]:
                        status = "LOW"
                    elif val > cfg["ref_max"]:
                        status = "HIGH"

                    results.append({
                        "test_name": name,
                        "test_code": cfg["code"],
                        "numeric_value": val,
                        "unit": cfg["unit"],
                        "ref_min": cfg["ref_min"],
                        "ref_max": cfg["ref_max"],
                        "status": status,
                        "confidence_score": 0.98,
                    })
                    matched_names.add(name)
                    break

        return results

    @classmethod
    def parse_vitals(cls, text: str) -> Dict[str, Any]:
        """Extract vital signs (Blood Pressure, Heart Rate, SpO2, Temp, RR, BMI)."""
        if not text:
            return {}

        norm_text = cls.normalize_text(text)
        vitals: Dict[str, Any] = {}

        # 1. Parse line-by-line for table structures
        for line in norm_text.splitlines():
            clean_line = line.strip("| \t")
            parts = [p.strip() for p in clean_line.split("|")]
            if len(parts) >= 2:
                name_part = parts[0].lower()
                val_part = parts[1].replace(",", "").strip()

                if "systolic" in name_part or "sbp" in name_part:
                    try:
                        vitals["sbp"] = int(float(val_part))
                    except ValueError:
                        pass
                elif "diastolic" in name_part or "dbp" in name_part:
                    try:
                        vitals["dbp"] = int(float(val_part))
                    except ValueError:
                        pass
                elif "heart rate" in name_part or "pulse" in name_part or "hr" in name_part:
                    try:
                        vitals["heart_rate"] = int(float(val_part))
                    except ValueError:
                        pass
                elif "spo2" in name_part or "oxygen" in name_part or "sat" in name_part:
                    try:
                        vitals["spo2"] = float(val_part)
                    except ValueError:
                        pass
                elif "respiratory" in name_part or "rr" in name_part or "respiration" in name_part:
                    try:
                        vitals["respiratory_rate"] = int(float(val_part))
                    except ValueError:
                        pass
                elif "temperature" in name_part or "temp" in name_part:
                    try:
                        val = float(val_part)
                        if val > 50.0:
                            val = (val - 32.0) * (5.0 / 9.0)
                        vitals["temperature_c"] = round(val, 1)
                    except ValueError:
                        pass

        # 2. Blood Pressure inline regex fallback: e.g. "120/80" or "BP 130/85"
        if "sbp" not in vitals:
            bp_match = re.search(r"(?:bp|blood pressure)?[\s:]*([0-9]{2,3})\s*[\/\\]\s*([0-9]{2,3})", norm_text, re.IGNORECASE)
            if bp_match:
                try:
                    vitals["sbp"] = int(bp_match.group(1))
                    vitals["dbp"] = int(bp_match.group(2))
                except ValueError:
                    pass

        # 3. Heart Rate inline regex fallback
        if "heart_rate" not in vitals:
            hr_match = re.search(r"(?:pulse|heart rate|hr)[\s:]*([0-9]{2,3})", norm_text, re.IGNORECASE)
            if hr_match:
                try:
                    vitals["heart_rate"] = int(hr_match.group(1))
                except ValueError:
                    pass

        # 4. SpO2 inline regex fallback
        if "spo2" not in vitals:
            spo2_match = re.search(r"(?:spo2|oxygen saturation|sat)[\s:]*([0-9]{2,3})\s*%?", norm_text, re.IGNORECASE)
            if spo2_match:
                try:
                    vitals["spo2"] = float(spo2_match.group(1))
                except ValueError:
                    pass

        # 5. Respiratory Rate inline regex fallback
        if "respiratory_rate" not in vitals:
            rr_match = re.search(r"(?:rr|respiratory rate|respiration)[\s:]*([0-9]{1,2})", norm_text, re.IGNORECASE)
            if rr_match:
                try:
                    vitals["respiratory_rate"] = int(rr_match.group(1))
                except ValueError:
                    pass

        # 6. Temperature inline regex fallback
        if "temperature_c" not in vitals:
            temp_match = re.search(r"(?:temp|temperature)[\s:]*([0-9]{2,3}\.?[0-9]*)", norm_text, re.IGNORECASE)
            if temp_match:
                try:
                    val = float(temp_match.group(1))
                    if val > 50.0:
                        val = (val - 32.0) * (5.0 / 9.0)
                    vitals["temperature_c"] = round(val, 1)
                except ValueError:
                    pass

        # Determine status
        status = "NORMAL"
        if vitals.get("spo2") and vitals["spo2"] < 90:
            status = "CRITICAL"
        elif vitals.get("sbp") and vitals["sbp"] > 180:
            status = "CRITICAL"
        elif vitals.get("sbp") and vitals["sbp"] > 130:
            status = "ABNORMAL"

        vitals["status"] = status
        return vitals

    @classmethod
    def parse_prescriptions(cls, text: str) -> List[Dict[str, Any]]:
        """
        Parses prescription medical text and extracts structured list of medications.
        Extracts: medicine_name, strength, dose, frequency, route, duration_days, instructions.
        """
        if not text:
            return []

        medicines: List[Dict[str, Any]] = []

        # Common medicine regex pattern
        # E.g. "Metformin 500mg - 1 tablet twice daily orally for 30 days"
        # E.g. "Tab Paracetamol 650 mg 1-0-1 after meals"
        # E.g. "Atorvastatin 10mg 1 tab OD at bedtime"
        med_patterns = [
            r"(?:Tab|Cap|Syr|Inj|T\.|C\.)?\s*([A-Z][a-z0-9\s]{2,30}?)\s+([0-9]+(?:\.[0-9]+)?\s*(?:mg|g|mcg|ml|IU|%))\s+([0-9\-\.\s]+(?:tab|tablet|cap|capsule|ml|pills?)?)?\s*([a-zA-Z0-9\-\s]{2,30}?)?(?:for\s+([0-9]+)\s*days?)?",
            r"(?:Rx|Prescription):\s*([A-Z][a-z0-9\s]{2,30}?)\s+([0-9]+(?:\.[0-9]+)?\s*(?:mg|g|mcg|ml))",
        ]

        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            for pattern in med_patterns:
                match = re.search(pattern, line_str, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    med_name = groups[0].strip()

                    # Clean prefix clutter
                    med_name = re.sub(r"^(?:Tab|Cap|Syr|Inj|T\.|C\.|Rx:?)\s*", "", med_name, flags=re.IGNORECASE).strip()

                    if len(med_name) >= 3 and not any(m["medicine_name"].lower() == med_name.lower() for m in medicines):
                        medicines.append({
                            "medicine_name": med_name.title(),
                            "strength": groups[1].strip() if len(groups) > 1 and groups[1] else None,
                            "dose": groups[2].strip() if len(groups) > 2 and groups[2] else "1 tablet",
                            "frequency": groups[3].strip() if len(groups) > 3 and groups[3] else "Once daily",
                            "route": "Oral",
                            "duration_days": int(groups[4]) if len(groups) > 4 and groups[4] and groups[4].isdigit() else 30,
                            "instructions": line_str,
                        })
                    break

        return medicines

