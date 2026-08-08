"""
Context Builder & System Safety Prompt Assembly Engine for ClinIQ Phase 5.

Assembles token-budgeted grounded context objects containing:
  - Patient Identity Context
  - Structured DB Evidence (Phase 4 analytics, parameters, vitals, medicines)
  - Unstructured RAG Document Chunks
  - Strict Medical System Prompts
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.modules.patients.schema import PatientRead
from app.observability.logger import get_logger

_log = get_logger(__name__)

# Base Grounded Medical Assistant System Prompt
CLINIQ_COPILOT_SYSTEM_PROMPT = """
You are the ClinIQ AI Copilot, a grounded clinical information assistant.
You provide clear, accurate summaries and answers strictly using the provided patient's stored medical records and evidence.

STRICT CLINICAL RULES:
1. Grounding: Answer ONLY from the supplied patient evidence. Do NOT invent missing clinical history or values.
2. Comprehensive Summarization: When requested to summarize or review a patient, organize all retrieved evidence into clear sections:
   - Patient & Demographics Overview
   - 8-Organ System Health Status
   - Key Lab Biomarkers
   - Active Clinical Alerts & Observations
3. No Diagnosis: You MUST NOT independently diagnose conditions from lab anomalies unless explicitly documented.
4. No Prescriptions: You MUST NOT prescribe medication, change dosages, or issue treatment protocols.
5. Absence of Specific Evidence: Only if specific requested data is missing, state that it is not documented in the available records. Do NOT refuse to summarize available records.
6. Provenance: Every patient claim must cite supporting evidence.
7. Concise & Professional: Respond in clean, professional clinical language with markdown headings and bullet points.
""".strip()


class GroundedContextPackage:
    """Packaged prompt & metadata container for GPT-5 Nano."""

    def __init__(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence_summary: str,
        sources: List[Dict[str, Any]],
        confidence_level: str,
    ) -> None:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.evidence_summary = evidence_summary
        self.sources = sources
        self.confidence_level = confidence_level


class ContextBuilder:
    """Constructs grounded context packages for GPT-5 Nano generation."""

    @classmethod
    def build_general_info_context(cls, query_text: str, target_medicine: Optional[str]) -> GroundedContextPackage:
        """Construct context for general medical knowledge questions."""
        sys_p = (
            "You are ClinIQ AI Copilot providing general medical information.\n"
            "Keep the response educational, concise, and clearly labeled as General Medical Information.\n"
            "State clearly that this is general information and not part of any specific patient's record."
        )
        user_p = f"General Medical Inquiry: {query_text}"
        return GroundedContextPackage(
            system_prompt=sys_p,
            user_prompt=user_p,
            evidence_summary="General Knowledge Request",
            sources=[],
            confidence_level="HIGH",
        )

    @classmethod
    def build_patient_grounded_context(
        cls,
        patient: PatientRead,
        query_text: str,
        intent_type: str,
        evidence_text: str,
        sources: List[Dict[str, Any]],
        confidence_level: str,
    ) -> GroundedContextPackage:
        """Construct context for patient-specific clinical queries."""
        p_header = (
            f"PATIENT IDENTITY:\n"
            f"Name: {patient.first_name} {patient.last_name}\n"
            f"MRN: {patient.mrn}\n"
            f"DOB: {patient.date_of_birth} | Gender: {patient.gender.title()} | Blood Group: {patient.blood_group or 'Unknown'}\n"
        )

        words = query_text.strip().split()
        if len(words) <= 3 or intent_type in ("PATIENT_SUMMARY", "HYBRID_QUERY") or any(w in query_text.lower() for w in ["summary", "overview", "who is", "profile"]):
            query_label = f"Provide a complete clinical summary for patient {patient.first_name} {patient.last_name}."
            instruction_text = (
                "INSTRUCTION: Synthesize a complete clinical summary for this patient from the retrieved evidence above. "
                "List all 8-organ system health scores, active clinical alerts, and key lab measurements in clear markdown sections."
            )
        else:
            query_label = query_text
            instruction_text = f"INSTRUCTION: Synthesize a clear, grounded answer to the clinician's question ('{query_text}') based strictly on the retrieved patient evidence above."

        user_p = (
            f"{p_header}\n"
            f"CLINICIAN REQUEST: {query_label}\n\n"
            f"RETRIEVED PATIENT EVIDENCE:\n"
            f"{evidence_text if evidence_text.strip() else 'No relevant records found.'}\n\n"
            f"{instruction_text}"
        )

        return GroundedContextPackage(
            system_prompt=CLINIQ_COPILOT_SYSTEM_PROMPT,
            user_prompt=user_p,
            evidence_summary=evidence_text,
            sources=sources,
            confidence_level=confidence_level,
        )
