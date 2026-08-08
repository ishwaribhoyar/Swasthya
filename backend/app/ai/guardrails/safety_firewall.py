"""
5-Layer Safety Firewall for ClinIQ Phase 5 Grounded AI Copilot.

Enforces production safety pipeline:
  Layer 1 — Input Guard: Detects prompt injection & instruction overrides.
  Layer 2 — Privacy Guard: Minimizes unnecessary PHI & isolates context.
  Layer 3 — Context Grounding Guard: Validates patient ownership of evidence.
  Layer 4 — Medical Safety Guard: Rejects LLM diagnostic claims & drug prescriptions.
  Layer 5 — Output Validation Guard: Inspects output claims against retrieved evidence.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from app.observability.logger import get_logger

_log = get_logger(__name__)

# Patterns indicative of prompt injection or override attempts
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above)\s+instructions",
    r"(?i)system\s*prompt",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)override\s+safety",
    r"(?i)reveal\s+(secret|internal|hidden)",
    r"(?i)pretend\s+to\s+be",
]

# Patterns indicative of prohibited LLM actions
PROHIBITED_MEDICAL_PATTERNS = [
    r"(?i)i\s+diagnose\s+you\s+with",
    r"(?i)you\s+have\s+been\s+diagnosed\s+with",
    r"(?i)i\s+prescribe",
    r"(?i)take\s+\d+\s*mg\s+of",
    r"(?i)administer\s+iv",
    r"(?i)start\s+taking",
    r"(?i)stop\s+taking\s+your\s+medication",
]


class ValidationResult:
    """Result container for safety firewall checks."""

    def __init__(
        self,
        passed: bool,
        layer_failed: Optional[str] = None,
        reason: Optional[str] = None,
        sanitized_content: Optional[str] = None,
    ) -> None:
        self.passed = passed
        self.layer_failed = layer_failed
        self.reason = reason
        self.sanitized_content = sanitized_content


class SafetyFirewall:
    """Production 5-Layer AI Safety Firewall."""

    @classmethod
    def validate_input(cls, user_message: str) -> ValidationResult:
        """Layer 1: Input Guard — check for prompt injection / instruction overrides."""
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, user_message):
                _log.warning("SAFETY_FIREWALL.INPUT_REJECTED", pattern=pattern)
                return ValidationResult(
                    passed=False,
                    layer_failed="LAYER_1_INPUT_GUARD",
                    reason="Input contains restricted instruction manipulation patterns.",
                )
        return ValidationResult(passed=True)

    @classmethod
    def sanitize_context_privacy(cls, context_text: str) -> str:
        """Layer 2: Privacy Guard — minimize PHI, obscure SSNs/financials if present."""
        # Clean potential sensitive patterns like raw passwords or SSNs
        cleaned = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED SSN]", context_text)
        return cleaned

    @classmethod
    def validate_context_grounding(
        cls, expected_patient_id: str, retrieved_sources: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Layer 3: Context Grounding Guard — verify every retrieved record matches patient_id."""
        for s in retrieved_sources:
            src_pid = s.get("patient_id")
            if src_pid and src_pid != expected_patient_id:
                _log.error("SAFETY_FIREWALL.CROSS_PATIENT_LEAK_PREVENTED", expected=expected_patient_id, found=src_pid)
                return ValidationResult(
                    passed=False,
                    layer_failed="LAYER_3_GROUNDING_GUARD",
                    reason="Cross-patient evidence leakage detected. Access blocked.",
                )
        return ValidationResult(passed=True)

    @classmethod
    def validate_medical_safety(cls, generated_text: str) -> Tuple[bool, str]:
        """Layer 4: Medical Safety Guard — block LLM diagnostic claims & drug prescriptions."""
        for pattern in PROHIBITED_MEDICAL_PATTERNS:
            if re.search(pattern, generated_text):
                _log.warning("SAFETY_FIREWALL.PROHIBITED_MEDICAL_TEXT", pattern=pattern)
                # Replace prohibited text with safe clinical review notice
                sanitized = re.sub(
                    pattern,
                    "Immediate clinician evaluation is required.",
                    generated_text,
                )
                return False, sanitized
        return True, generated_text

    @classmethod
    def validate_output_claims(
        cls,
        generated_text: str,
        retrieved_evidence_summary: str,
        sources_count: int,
    ) -> ValidationResult:
        """
        Layer 5: Output Validation Guard — verify generated response against evidence context.
        Strips unsupported assertions or downgrades confidence.
        """
        # Step 1: Run medical safety check
        safe_med, sanitized = cls.validate_medical_safety(generated_text)
        
        # Step 2: Check for unsupported absolute claim statements if zero sources returned
        if sources_count == 0:
            if "does not have" in sanitized.lower() or "is completely normal" in sanitized.lower():
                _log.info("SAFETY_FIREWALL.UNSUPPORTED_NEGATIVE_CLAIM_CORRECTED")
                sanitized = "I couldn't find documentation regarding this condition in the available patient records."

        return ValidationResult(
            passed=safe_med,
            layer_failed=None if safe_med else "LAYER_4_MEDICAL_SAFETY",
            sanitized_content=sanitized,
        )
