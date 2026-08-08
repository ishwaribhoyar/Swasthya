"""
Patient Resolution Engine for Swasthya Phase 5.

Resolves patient references (Name, MRN, ID) against SQLite.
Supports:
  1. Patient-Scoped Mode (explicit patient_id supplied)
  2. Global Mode (name or MRN mentioned in query string)

Enforces strict clinician isolation (patient.clinician_id == JWT.sub).
Handles ambiguous matching (returns candidate list if multiple match).
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient
from app.modules.patients.service import PatientService
from app.modules.patients.schema import PatientRead
from app.observability.logger import get_logger

_log = get_logger(__name__)


class PatientResolutionResult:
    """Resolution status container."""

    def __init__(
        self,
        status: str,  # RESOLVED, AMBIGUOUS, NOT_FOUND, UNAUTHORIZED
        patient: Optional[PatientRead] = None,
        candidates: Optional[List[PatientRead]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.status = status
        self.patient = patient
        self.candidates = candidates or []
        self.message = message


class PatientResolver:
    """Resolves patient identity securely against SQLite DB."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._patient_service = PatientService(session)

    async def resolve_patient(
        self,
        query_text: str,
        clinician_id: str,
        explicit_patient_id: Optional[str] = None,
    ) -> PatientResolutionResult:
        """
        Resolve patient identity by ID, MRN, or Name.
        Strictly scoped to clinician_id.
        """
        # Fetch all active patients for this clinician
        stmt = select(Patient).where(
            Patient.clinician_id == clinician_id,
            Patient.is_active == True,
        )
        res = await self._session.execute(stmt)
        all_patients = res.scalars().all()

        if not all_patients:
            return PatientResolutionResult(
                status="NOT_FOUND",
                message="No active patient records found in your account.",
            )

        query_lower = query_text.lower()

        # Check MRN pattern MRN-...
        mrn_match = re.search(r"\bMRN-[A-Za-z0-9-]+\b", query_text, re.IGNORECASE)
        if mrn_match:
            mrn_str = mrn_match.group(0).upper()
            for p in all_patients:
                if p.mrn.upper() == mrn_str:
                    return PatientResolutionResult(
                        status="RESOLVED",
                        patient=self._patient_service._to_read(p),
                    )

        # Name Search from query text
        matched: List[Patient] = []
        for p in all_patients:
            full_name = f"{p.first_name} {p.last_name}".lower()
            if (
                full_name in query_lower
                or p.first_name.lower() in query_lower
                or p.last_name.lower() in query_lower
            ):
                matched.append(p)

        if len(matched) == 1:
            return PatientResolutionResult(
                status="RESOLVED",
                patient=self._patient_service._to_read(matched[0]),
            )
        elif len(matched) > 1:
            candidates = [self._patient_service._to_read(m) for m in matched]
            return PatientResolutionResult(
                status="AMBIGUOUS",
                candidates=candidates,
                message=f"Multiple patients match your query ({len(candidates)} candidates). Please select the correct patient.",
            )

        # Check generic roster / list queries (e.g. "tell about anyone in db", "show patients", "who is in db")
        generic_keywords = ["anyone", "everyone", "all patients", "roster", "database", "in db", "list patients", "who is in", "show patients"]
        is_generic_roster_query = any(kw in query_lower for kw in generic_keywords)

        if is_generic_roster_query:
            candidates = [self._patient_service._to_read(m) for m in all_patients]
            return PatientResolutionResult(
                status="AMBIGUOUS",
                candidates=candidates,
                message=f"Here are the active patient records in your roster ({len(candidates)} patients available). Please select a patient to view their grounded clinical summary:",
            )

        # Fallback 1: Use explicit_patient_id if supplied from page context
        if explicit_patient_id:
            for p in all_patients:
                if p.id == explicit_patient_id:
                    return PatientResolutionResult(
                        status="RESOLVED",
                        patient=self._patient_service._to_read(p),
                    )

        # Fallback 2: If clinician has exactly 1 patient, auto-resolve to that patient
        if len(all_patients) == 1:
            _log.info("PATIENT_RESOLVER.SINGLE_PATIENT_AUTO_RESOLVED", patient_id=all_patients[0].id)
            return PatientResolutionResult(
                status="RESOLVED",
                patient=self._patient_service._to_read(all_patients[0]),
            )

        # Fallback 3: Return selectable candidate list for all active patients
        candidates = [self._patient_service._to_read(m) for m in all_patients]
        return PatientResolutionResult(
            status="AMBIGUOUS",
            candidates=candidates,
            message=f"Please select which patient you would like to query ({len(candidates)} active patients found in your roster):",
        )
