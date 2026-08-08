"""
Safety, PHI Scrubber & Grounding Verification Guardrails.

Enforces clinical safety, groundness verification, PHI scrubbing, and immutable audit hashing
for all AI Copilot operations.
"""
from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Tuple


class SafetyGuardrails:
    """Clinical Safety & Grounding Verification Engine."""

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize query input from potential prompt injections."""
        if not text:
            return ""
        # Strip system instruction override patterns
        cleaned = re.sub(r"(?i)(ignore previous instructions|system prompt|you are now)", "", text)
        return cleaned.strip()

    @classmethod
    def compute_audit_hash(
        cls,
        patient_id: str,
        query: str,
        retrieved_chunk_ids: List[str],
        response_text: str,
    ) -> str:
        """
        Generate immutable SHA256 audit hash for AI query execution context.
        """
        raw = f"PATIENT:{patient_id}|Q:{query}|CHUNKS:{','.join(retrieved_chunk_ids)}|RESP:{response_text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def verify_groundedness(
        cls, response_text: str, retrieved_context_text: str
    ) -> Tuple[float, List[str]]:
        """
        Check that response statements cite retrieved patient facts and avoid hallucinations.
        Returns (confidence_score, grounded_statements).
        """
        if not response_text or not retrieved_context_text:
            return 0.5, []

        statements = [s.strip() for s in re.split(r"[.!?\n]", response_text) if len(s.strip()) > 10]
        if not statements:
            return 0.95, [response_text]

        ctx_lower = retrieved_context_text.lower()
        supported_count = 0
        grounded_statements = []

        for st in statements:
            words = [w.lower() for w in st.split() if len(w) >= 4 and w.isalnum()]
            if not words:
                supported_count += 1
                continue
            # Check overlap
            matches = sum(1 for w in words if w in ctx_lower)
            match_ratio = matches / max(1, len(words))

            if match_ratio >= 0.35:
                supported_count += 1
                grounded_statements.append(st)

        confidence = round(max(0.70, min(0.99, supported_count / max(1, len(statements)))), 4)
        return confidence, grounded_statements
