"""
Query Router & Intent Classification Engine for ClinIQ Phase 5.

Classifies incoming clinician queries into specific intents:
  - PATIENT_SUMMARY
  - TREND_QUERY
  - MEDICINE_QUERY
  - MEDICINE_FREQUENCY_QUERY
  - VITAL_QUERY
  - ORGAN_SCORE_QUERY
  - ALERT_QUERY
  - TIMELINE_QUERY
  - CLINICAL_NOTE_QUERY
  - GENERAL_MEDICAL_INFORMATION

Determines Retrieval Strategy (STRUCTURED vs UNSTRUCTURED vs HYBRID).
Decomposes complex multi-part questions.
"""
from __future__ import annotations

import re
from typing import List, Tuple, Optional
from app.observability.logger import get_logger

_log = get_logger(__name__)


class QueryIntent:
    """Parsed query intent metadata."""

    def __init__(
        self,
        intent_type: str,
        retrieval_pathway: str,  # STRUCTURED, UNSTRUCTURED, HYBRID, GENERAL
        target_parameter: Optional[str] = None,
        target_medicine: Optional[str] = None,
        is_general_info: bool = False,
    ) -> None:
        self.intent_type = intent_type
        self.retrieval_pathway = retrieval_pathway
        self.target_parameter = target_parameter
        self.target_medicine = target_medicine
        self.is_general_info = is_general_info


class QueryRouter:
    """Classifies clinician questions and assigns retrieval pathway."""

    @classmethod
    def classify_query(cls, query_text: str) -> QueryIntent:
        q_lower = query_text.strip().lower()

        # 1. General Medical Knowledge queries (e.g. "What is metformin used for?")
        if (
            re.search(r"(?i)\bwhat is\s+[a-z0-9]+\s+(used for|indicated for|prescribed for)\b", query_text)
            or re.search(r"(?i)\bexplain\s+(the\s+)?(use|side effects|mechanism)\s+of\b", query_text)
        ):
            med_m = re.search(r"(?i)\b(metformin|paracetamol|dolo|amlodipine|atorvastatin|pantoprazole|aspirin)\b", query_text)
            target_med = med_m.group(1) if med_m else None
            return QueryIntent(
                intent_type="GENERAL_MEDICAL_INFORMATION",
                retrieval_pathway="GENERAL",
                target_medicine=target_med,
                is_general_info=True,
            )

        # 2. Patient Summary queries (single name keyword, "summary", "overview", "tell me about", short name input)
        words = q_lower.split()
        if (
            len(words) <= 3 and not any(w in q_lower for w in ["what", "how", "why", "when", "is", "has", "does", "where"])
        ) or any(w in q_lower for w in ["summary", "overview", "tell me about", "profile", "history", "report", "case"]):
            return QueryIntent(
                intent_type="PATIENT_SUMMARY",
                retrieval_pathway="STRUCTURED",
            )

        # 3. Medicine Frequency Queries (e.g. "How many times was metformin prescribed?")
        if "how many times" in q_lower and ("prescribed" in q_lower or "given" in q_lower or "medicine" in q_lower):
            med_m = re.search(r"(?i)\b(metformin|paracetamol|dolo|amlodipine|atorvastatin|pantoprazole|aspirin|pcm)\b", query_text)
            target_med = med_m.group(1) if med_m else None
            return QueryIntent(
                intent_type="MEDICINE_FREQUENCY_QUERY",
                retrieval_pathway="STRUCTURED",
                target_medicine=target_med,
            )

        # 4. Medicine History Queries
        if any(w in q_lower for w in ["medicine", "medication", "drug", "prescription", "prescribed", "dosage"]):
            med_m = re.search(r"(?i)\b(metformin|paracetamol|dolo|amlodipine|atorvastatin|pantoprazole|aspirin|pcm)\b", query_text)
            target_med = med_m.group(1) if med_m else None
            return QueryIntent(
                intent_type="MEDICINE_QUERY",
                retrieval_pathway="STRUCTURED",
                target_medicine=target_med,
            )

        # 5. Trend & Anomaly Queries (e.g. "Has kidney function worsened?", "Is glucose increasing?")
        if any(w in q_lower for w in ["worsened", "increased", "decreased", "trend", "improving", "changing", "higher", "lower", "rising", "falling"]):
            param_m = re.search(r"(?i)\b(creatinine|potassium|glucose|hb|hemoglobin|bp|blood pressure|wbc|hba1c)\b", query_text)
            target_param = param_m.group(1) if param_m else None
            return QueryIntent(
                intent_type="TREND_QUERY",
                retrieval_pathway="STRUCTURED",
                target_parameter=target_param,
            )

        # 6. Organ System Queries
        if any(w in q_lower for w in ["organ", "renal", "kidney", "electrolyte", "cardiovascular", "heart", "hepatic", "liver"]):
            return QueryIntent(
                intent_type="ORGAN_SCORE_QUERY",
                retrieval_pathway="STRUCTURED",
            )

        # 7. Vitals Queries
        if any(w in q_lower for w in ["bp", "blood pressure", "pulse", "heart rate", "spo2", "vital"]):
            return QueryIntent(
                intent_type="VITAL_QUERY",
                retrieval_pathway="STRUCTURED",
            )

        # 8. Alerts Queries
        if any(w in q_lower for w in ["alert", "warning", "critical", "finding", "abnormal"]):
            return QueryIntent(
                intent_type="ALERT_QUERY",
                retrieval_pathway="STRUCTURED",
            )

        # 9. Unstructured Clinical Notes & Consultation Queries
        if any(w in q_lower for w in ["note", "consultation", "doctor", "observation", "complaint", "history of", "discharge", "report text"]):
            return QueryIntent(
                intent_type="CLINICAL_NOTE_QUERY",
                retrieval_pathway="UNSTRUCTURED",
            )

        # Default Fallback: Hybrid Retrieval
        return QueryIntent(
            intent_type="HYBRID_QUERY",
            retrieval_pathway="HYBRID",
        )
