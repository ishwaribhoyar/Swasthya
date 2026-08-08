"""
Automated Clinical Alert & Severity Engine.
Generates real-time clinical alerts flagging parameter anomalies for clinician review.
Does NOT output prescriptive drug treatment protocols.
"""
from __future__ import annotations

from typing import Dict, List, Any


class AlertEngine:
    """Evaluates parameters against clinical risk cutoffs for decision support."""

    @staticmethod
    def generate_alerts(labs: List[Dict[str, Any]], vitals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate parameters against clinical risk cutoffs."""
        alerts: List[Dict[str, Any]] = []

        # 1. SpO2 Critical Hypoxia Alert
        if vitals.get("spo2") and vitals["spo2"] < 90:
            alerts.append({
                "alert_type": "vital_critical",
                "severity": "CRITICAL",
                "title": "Critical Hypoxia Alert (SpO2 < 90%)",
                "message": f"Observed SpO2 is {vitals['spo2']}%. Reference range: 95 - 100%.",
                "biomarker_name": "SpO2",
                "observed_value": f"{vitals['spo2']}%",
                "reference_range": "95 - 100%",
                "action_recommendation": "Immediate clinician review required. Evaluate respiratory status and clinical context.",
            })

        # 2. Hypertensive Crisis Alert
        if vitals.get("sbp") and vitals["sbp"] >= 180:
            alerts.append({
                "alert_type": "vital_critical",
                "severity": "CRITICAL",
                "title": "Hypertensive Elevation Warning (SBP >= 180 mmHg)",
                "message": f"Recorded Systolic Blood Pressure is {vitals['sbp']} mmHg. Reference range: 90 - 120 mmHg.",
                "biomarker_name": "Systolic BP",
                "observed_value": f"{vitals['sbp']} mmHg",
                "reference_range": "90 - 120 mmHg",
                "action_recommendation": "Immediate clinician review required. Evaluate blood pressure elevation and cardiovascular history.",
            })

        # 3. Lab Critical Alerts
        for lab in labs:
            name = lab.get("test_name", "")
            val = lab.get("numeric_value", 0.0)
            status = lab.get("status", "NORMAL")
            unit = lab.get("unit", "")
            ref_min = lab.get("ref_min", "")
            ref_max = lab.get("ref_max", "")
            ref_str = f"{ref_min} - {ref_max} {unit}".strip() if ref_min and ref_max else "Standard Reference Range"

            is_potassium = any(k in name.lower() for k in ["potassium", "k+", "serum potassium"])
            is_troponin = "troponin" in name.lower()
            is_platelets = "platelet" in name.lower()
            is_glucose = any(g in name.lower() for g in ["fasting glucose", "serum glucose", "random glucose", "blood glucose"]) and "hba1c" not in name.lower()
            is_hemoglobin = (
                ("hemoglobin" in name.lower() or "haemoglobin" in name.lower() or name.lower().strip() == "hb")
                and "hba1c" not in name.lower()
                and "a1c" not in name.lower()
            )

            if is_potassium and val >= 6.0:
                alerts.append({
                    "alert_type": "lab_critical",
                    "severity": "CRITICAL",
                    "title": "Severe Hyperkalemia Warning (Potassium >= 6.0 mEq/L)",
                    "message": f"Serum Potassium level is {val} {unit or 'mEq/L'}. Reference cutoff: >= 6.0 mEq/L.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit or 'mEq/L'}",
                    "reference_range": ref_str or "3.5 - 5.0 mEq/L",
                    "action_recommendation": "CRITICAL: Severe hyperkalemia-range value detected. Immediate clinician review required.",
                })
            elif is_troponin and val > 0.04:
                alerts.append({
                    "alert_type": "lab_critical",
                    "severity": "CRITICAL",
                    "title": "Elevated Cardiac Troponin Warning",
                    "message": f"Serum Troponin level is {val} {unit or 'ng/mL'}. Reference cutoff: < 0.04 ng/mL.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit or 'ng/mL'}",
                    "reference_range": "< 0.04 ng/mL",
                    "action_recommendation": "CRITICAL: Elevated cardiac biomarker detected. Immediate clinician review required.",
                })
            elif is_platelets and val < 50.0:
                alerts.append({
                    "alert_type": "lab_critical",
                    "severity": "CRITICAL",
                    "title": "Severe Thrombocytopenia Alert (PLT < 50 k/uL)",
                    "message": f"Platelet count is {val} {unit or 'k/uL'}. Reference range: 150 - 450 k/uL.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit or 'k/uL'}",
                    "reference_range": "150 - 450 k/uL",
                    "action_recommendation": "CRITICAL: Severe low platelet count detected. Immediate clinician review required.",
                })
            elif is_glucose and val >= 250.0:
                alerts.append({
                    "alert_type": "lab_critical",
                    "severity": "HIGH",
                    "title": "Severe Hyperglycemia Alert (Glucose >= 250 mg/dL)",
                    "message": f"Glucose level is {val} {unit or 'mg/dL'}. Reference range: 70 - 99 mg/dL.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit or 'mg/dL'}",
                    "reference_range": ref_str or "70 - 99 mg/dL",
                    "action_recommendation": "HIGH: Elevated glucose level detected. Clinician review recommended.",
                })
            elif is_hemoglobin and val < 8.0:
                alerts.append({
                    "alert_type": "lab_critical",
                    "severity": "HIGH",
                    "title": "Severe Anemia Alert (Hb < 8.0 g/dL)",
                    "message": f"Hemoglobin is {val} {unit or 'g/dL'}. Reference range: 12.0 - 17.5 g/dL.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit or 'g/dL'}",
                    "reference_range": ref_str or "12.0 - 17.5 g/dL",
                    "action_recommendation": "HIGH: Low hemoglobin level detected. Clinician review recommended.",
                })
            elif status in ["HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW"]:
                alerts.append({
                    "alert_type": "lab_abnormal",
                    "severity": "MODERATE" if "CRITICAL" not in status else "HIGH",
                    "title": f"Abnormal {name} ({status.replace('_', ' ')})",
                    "message": f"Observed value for {name} is {val} {unit}.",
                    "biomarker_name": name,
                    "observed_value": f"{val} {unit}",
                    "reference_range": ref_str,
                    "action_recommendation": "Abnormal lab value detected. Clinician review recommended on follow-up.",
                })

        return alerts
