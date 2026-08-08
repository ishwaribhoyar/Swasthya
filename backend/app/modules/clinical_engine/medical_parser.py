"""
Deterministic LOINC-aligned Medical Lab Result Parser & Vitals Extractor.
Parses raw extracted text/HTML into validated physiological metrics.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

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
        "patterns": [r"white blood cell", r"\bwbc\b", r"leukocytes"],
        "unit": "k/uL",
        "ref_min": 4.5,
        "ref_max": 11.0,
        "critical_low": 2.0,
        "critical_high": 30.0,
    },
    "Platelets": {
        "code": "777-3",
        "patterns": [r"platelets", r"\bplt\b", r"platelet count"],
        "unit": "k/uL",
        "ref_min": 150.0,
        "ref_max": 450.0,
        "critical_low": 50.0,
        "critical_high": 1000.0,
    },
    "Serum Glucose": {
        "code": "2345-7",
        "patterns": [r"serum glucose", r"blood glucose", r"fasting glucose", r"\bglucose\b"],
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
        "patterns": [r"serum creatinine", r"creatinine"],
        "unit": "mg/dL",
        "ref_min": 0.6,
        "ref_max": 1.2,
        "critical_low": 0.2,
        "critical_high": 3.0,
    },
    "BUN": {
        "code": "3094-0",
        "patterns": [r"blood urea nitrogen", r"\bbun\b", r"urea nitrogen"],
        "unit": "mg/dL",
        "ref_min": 7.0,
        "ref_max": 20.0,
        "critical_low": 3.0,
        "critical_high": 60.0,
    },
    "eGFR": {
        "code": "33914-3",
        "patterns": [r"egfr", r"gfr", r"estimated gfr"],
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
    def parse_labs(cls, text: str) -> List[Dict[str, Any]]:
        """Extract lab test values from text using clinical regex patterns."""
        results: List[Dict[str, Any]] = []

        for name, cfg in LAB_CONFIG.items():
            for pat in cfg["patterns"]:
                # Match "Hemoglobin: 14.2 g/dL" or "Hb 14.2"
                regex = re.compile(rf"{pat}[:\s=]+([0-9]+\.?[0-9]*)", re.IGNORECASE)
                match = regex.search(text)
                if match:
                    try:
                        val = float(match.group(1))
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
                        break
                    except ValueError:
                        continue

        return results

    @classmethod
    def parse_vitals(cls, text: str) -> Dict[str, Any]:
        """Extract vital signs (Blood Pressure, Heart Rate, SpO2, Temp, RR, BMI)."""
        vitals: Dict[str, Any] = {}

        # 1. Blood Pressure: e.g. "120/80" or "BP 130/85"
        bp_match = re.search(r"(?:bp|blood pressure)?[\s:]*([0-9]{2,3})\s*[\/\\]\s*([0-9]{2,3})", text, re.IGNORECASE)
        if bp_match:
            try:
                vitals["sbp"] = int(bp_match.group(1))
                vitals["dbp"] = int(bp_match.group(2))
            except ValueError:
                pass

        # 2. Heart Rate / Pulse: e.g. "Pulse 72 bpm" or "HR: 80"
        hr_match = re.search(r"(?:pulse|heart rate|hr)[\s:]*([0-9]{2,3})", text, re.IGNORECASE)
        if hr_match:
            try:
                vitals["heart_rate"] = int(hr_match.group(1))
            except ValueError:
                pass

        # 3. SpO2: e.g. "SpO2 98%" or "Oxygen Saturation: 96%"
        spo2_match = re.search(r"(?:spo2|oxygen saturation|sat)[\s:]*([0-9]{2,3})\s*%?", text, re.IGNORECASE)
        if spo2_match:
            try:
                vitals["spo2"] = float(spo2_match.group(1))
            except ValueError:
                pass

        # 4. Respiratory Rate: e.g. "RR 16" or "Respiration: 18"
        rr_match = re.search(r"(?:rr|respiratory rate|respiration)[\s:]*([0-9]{1,2})", text, re.IGNORECASE)
        if rr_match:
            try:
                vitals["respiratory_rate"] = int(rr_match.group(1))
            except ValueError:
                pass

        # 5. Temperature: e.g. "Temp 37.0 C" or "98.6 F"
        temp_match = re.search(r"(?:temp|temperature)[\s:]*([0-9]{2,3}\.?[0-9]*)", text, re.IGNORECASE)
        if temp_match:
            try:
                val = float(temp_match.group(1))
                # Convert F to C if > 50
                if val > 50.0:
                    val = (val - 32.0) * (5.0 / 9.0)
                vitals["temperature_c"] = round(val, 1)
            except ValueError:
                pass

        # 6. BMI: e.g. "BMI 24.5"
        bmi_match = re.search(r"\bbmi[\s:]*([0-9]{2}\.?[0-9]*)", text, re.IGNORECASE)
        if bmi_match:
            try:
                vitals["bmi"] = float(bmi_match.group(1))
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
