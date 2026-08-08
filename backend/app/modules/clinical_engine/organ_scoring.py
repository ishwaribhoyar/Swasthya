"""
Multi-Organ System Health Scoring Engine (8 Organ Systems).

Calculates deterministic organ health scores across 8 body systems.
If no parameters exist for a system, returns score=None and status='INSUFFICIENT_DATA'.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any, Optional


class OrganScoringEngine:
    """Calculates organ health scores across 8 body systems."""

    @staticmethod
    def calculate_scores(labs: List[Dict[str, Any]], vitals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate 8 organ system scores from labs & vitals dictionary."""
        lab_list = labs or []
        vitals_dict = vitals or {}

        scores: List[Dict[str, Any]] = []

        # Helper to find lab matching names
        def find_labs(keys: List[str]) -> List[Dict[str, Any]]:
            matched = []
            for l in lab_list:
                tname = l.get("test_name", "").lower()
                if any(k.lower() in tname for k in keys):
                    matched.append(l)
            return matched

        # 1. Cardiovascular System (BP, Heart Rate, Troponin)
        card_biomarkers = []
        card_deductions = 0.0
        if vitals_dict.get("sbp"):
            card_biomarkers.append("Systolic BP")
            sbp = vitals_dict["sbp"]
            if sbp >= 180:
                card_deductions += 60.0
            elif sbp > 130:
                card_deductions += 20.0
        if vitals_dict.get("heart_rate"):
            card_biomarkers.append("Heart Rate")
            hr = vitals_dict["heart_rate"]
            if hr > 110 or hr < 50:
                card_deductions += 20.0

        trop_labs = find_labs(["troponin"])
        if trop_labs:
            card_biomarkers.append("Troponin")
            if any(l.get("numeric_value", 0.0) > 0.04 for l in trop_labs):
                card_deductions += 70.0

        if not card_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("cardiovascular", "Cardiovascular"))
        else:
            c_score = max(0.0, 100.0 - card_deductions)
            scores.append({
                "organ_system": "cardiovascular",
                "score": c_score,
                "status": OrganScoringEngine._get_status(c_score),
                "contributing_biomarkers": json.dumps(card_biomarkers),
                "rationale": f"Evaluated based on {', '.join(card_biomarkers)}.",
            })

        # 2. Electrolyte Balance (Potassium, Sodium, Chloride, Calcium)
        elec_biomarkers = []
        elec_deductions = 0.0

        k_labs = find_labs(["potassium", "k+", "serum potassium"])
        if k_labs:
            elec_biomarkers.append("Serum Potassium")
            for kl in k_labs:
                val = kl.get("numeric_value", 0.0)
                st = kl.get("status", "")
                if val >= 6.0 or val <= 2.8 or "CRITICAL" in st:
                    elec_deductions += 70.0
                elif val > 5.0 or val < 3.5 or st in ["HIGH", "LOW"]:
                    elec_deductions += 30.0

        na_labs = find_labs(["sodium", "na+", "serum sodium"])
        if na_labs:
            elec_biomarkers.append("Serum Sodium")
            for nl in na_labs:
                st = nl.get("status", "")
                if "CRITICAL" in st:
                    elec_deductions += 40.0
                elif st in ["HIGH", "LOW"]:
                    elec_deductions += 20.0

        ca_labs = find_labs(["calcium", "ca2+"])
        if ca_labs:
            elec_biomarkers.append("Serum Calcium")
            for cl in ca_labs:
                if cl.get("status", "") != "NORMAL":
                    elec_deductions += 20.0

        if not elec_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("electrolyte", "Electrolyte"))
        else:
            e_score = max(0.0, 100.0 - elec_deductions)
            scores.append({
                "organ_system": "electrolyte",
                "score": e_score,
                "status": OrganScoringEngine._get_status(e_score),
                "contributing_biomarkers": json.dumps(elec_biomarkers),
                "rationale": f"Electrolyte balance evaluated via {', '.join(elec_biomarkers)}.",
            })

        # 3. Hematological System (Hemoglobin, WBC, Platelets, RBC, Hematocrit)
        hem_biomarkers = []
        hem_deductions = 0.0
        for b_name, b_keys in [("Hemoglobin", ["hemoglobin", "hb"]), ("WBC", ["wbc", "leukocyte"]), ("Platelets", ["platelet", "plt"]), ("RBC", ["rbc"])]:
            h_labs = find_labs(b_keys)
            if h_labs:
                hem_biomarkers.append(b_name)
                for hl in h_labs:
                    st = hl.get("status", "")
                    if "CRITICAL" in st:
                        hem_deductions += 35.0
                    elif st in ["HIGH", "LOW"]:
                        hem_deductions += 15.0

        if not hem_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("hematological", "Hematological"))
        else:
            h_score = max(0.0, 100.0 - hem_deductions)
            scores.append({
                "organ_system": "hematological",
                "score": h_score,
                "status": OrganScoringEngine._get_status(h_score),
                "contributing_biomarkers": json.dumps(hem_biomarkers),
                "rationale": f"Hematological indices assessed via {', '.join(hem_biomarkers)}.",
            })

        # 4. Hepatic System (ALT, AST, Bilirubin, ALP)
        hep_biomarkers = []
        hep_deductions = 0.0
        for b_name, b_keys in [("ALT", ["alt", "sgpt"]), ("AST", ["ast", "sgot"]), ("Bilirubin", ["bilirubin"]), ("ALP", ["alkaline phosphatase", "alp"])]:
            hp_labs = find_labs(b_keys)
            if hp_labs:
                hep_biomarkers.append(b_name)
                for hpl in hp_labs:
                    st = hpl.get("status", "")
                    if "CRITICAL" in st:
                        hep_deductions += 35.0
                    elif st in ["HIGH", "LOW"]:
                        hep_deductions += 20.0

        if not hep_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("hepatic", "Hepatic"))
        else:
            hp_score = max(0.0, 100.0 - hep_deductions)
            scores.append({
                "organ_system": "hepatic",
                "score": hp_score,
                "status": OrganScoringEngine._get_status(hp_score),
                "contributing_biomarkers": json.dumps(hep_biomarkers),
                "rationale": f"Hepatic panel evaluated via {', '.join(hep_biomarkers)}.",
            })

        # 5. Inflammatory System (CRP, ESR, WBC)
        inf_biomarkers = []
        inf_deductions = 0.0
        crp_labs = find_labs(["crp", "c-reactive"])
        if crp_labs:
            inf_biomarkers.append("CRP")
            for cl in crp_labs:
                if cl.get("numeric_value", 0.0) > 3.0:
                    inf_deductions += 35.0

        if not inf_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("inflammatory", "Inflammatory"))
        else:
            inf_score = max(0.0, 100.0 - inf_deductions)
            scores.append({
                "organ_system": "inflammatory",
                "score": inf_score,
                "status": OrganScoringEngine._get_status(inf_score),
                "contributing_biomarkers": json.dumps(inf_biomarkers),
                "rationale": f"Systemic inflammation calculated via {', '.join(inf_biomarkers)}.",
            })

        # 6. Metabolic & Endocrine (Glucose, HbA1c, Cholesterol, LDL, HDL, Triglycerides)
        met_biomarkers = []
        met_deductions = 0.0
        for b_name, b_keys in [("Glucose", ["glucose", "sugar"]), ("HbA1c", ["hba1c"]), ("Cholesterol", ["cholesterol", "ldl", "hdl", "triglyceride"])]:
            m_labs = find_labs(b_keys)
            if m_labs:
                met_biomarkers.append(b_name)
                for ml in m_labs:
                    st = ml.get("status", "")
                    if "CRITICAL" in st:
                        met_deductions += 35.0
                    elif st in ["HIGH", "LOW"]:
                        met_deductions += 20.0

        if not met_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("metabolic", "Metabolic"))
        else:
            m_score = max(0.0, 100.0 - met_deductions)
            scores.append({
                "organ_system": "metabolic",
                "score": m_score,
                "status": OrganScoringEngine._get_status(m_score),
                "contributing_biomarkers": json.dumps(met_biomarkers),
                "rationale": f"Metabolic status evaluated via {', '.join(met_biomarkers)}.",
            })

        # 7. Renal System (Creatinine, Urea, BUN, eGFR)
        ren_biomarkers = []
        ren_deductions = 0.0
        for b_name, b_keys in [("Creatinine", ["creatinine"]), ("Urea", ["urea", "bun"]), ("eGFR", ["egfr"])]:
            r_labs = find_labs(b_keys)
            if r_labs:
                ren_biomarkers.append(b_name)
                for rl in r_labs:
                    st = rl.get("status", "")
                    if "CRITICAL" in st:
                        ren_deductions += 45.0
                    elif st in ["HIGH", "LOW"]:
                        ren_deductions += 25.0

        if not ren_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("renal", "Renal"))
        else:
            r_score = max(0.0, 100.0 - ren_deductions)
            scores.append({
                "organ_system": "renal",
                "score": r_score,
                "status": OrganScoringEngine._get_status(r_score),
                "contributing_biomarkers": json.dumps(ren_biomarkers),
                "rationale": f"Renal function assessed via {', '.join(ren_biomarkers)}.",
            })

        # 8. Respiratory System (SpO2, Respiratory Rate)
        resp_biomarkers = []
        resp_deductions = 0.0
        if vitals_dict.get("spo2"):
            resp_biomarkers.append("SpO2")
            spo2 = vitals_dict["spo2"]
            if spo2 < 90:
                resp_deductions += 60.0
            elif spo2 < 95:
                resp_deductions += 25.0

        if not resp_biomarkers:
            scores.append(OrganScoringEngine._build_insufficient_score("respiratory", "Respiratory"))
        else:
            rsp_score = max(0.0, 100.0 - resp_deductions)
            scores.append({
                "organ_system": "respiratory",
                "score": rsp_score,
                "status": OrganScoringEngine._get_status(rsp_score),
                "contributing_biomarkers": json.dumps(resp_biomarkers),
                "rationale": f"Respiratory status calculated via {', '.join(resp_biomarkers)}.",
            })

        return scores

    @staticmethod
    def _build_insufficient_score(system_key: str, system_name: str) -> Dict[str, Any]:
        return {
            "organ_system": system_key,
            "score": None,
            "status": "INSUFFICIENT_DATA",
            "contributing_biomarkers": json.dumps([]),
            "rationale": f"Insufficient clinical measurements available to score {system_name} system.",
        }

    @staticmethod
    def _get_status(score: float) -> str:
        if score >= 85.0:
            return "OPTIMAL"
        elif score >= 70.0:
            return "MILD_STRAIN"
        elif score >= 50.0:
            return "MODERATE_IMPAIRMENT"
        return "SEVERE_DYSFUNCTION"
