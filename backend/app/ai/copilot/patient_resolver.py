"""
Patient Resolution Engine for ClinIQ Phase 5.

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
        # Mode 1: Explicit Patient ID supplied (Patient Detail view)
        if explicit_patient_id:
            stmt = select(Patient).where(
                Patient.id == explicit_patient_id,
                Patient.clinician_id == clinician_id,
            )
            res = await self._session.execute(stmt)
            p = res.scalar_one_or_none()

            if not p:
                _log.warning("PATIENT_RESOLVER.EXPLICIT_ID_UNAUTHORIZED", patient_id=explicit_patient_id)
                return PatientResolutionResult(
                    status="NOT_FOUND",
                    message="Patient not found or unauthorized.",
                )
            
            return PatientResolutionResult(
                status="RESOLVED",
                patient=self._patient_service._to_read(p),
            )

        # Mode 2: Global Search from Query String (Name or MRN)
        # Check MRN pattern MRN-YYYY-XXXXXX
        mrn_match = re.search(r"\bMRN-\d{4}-\d{6}\b", query_text, re.IGNORECASE)
        if mrn_match:
            mrn_str = mrn_match.group(0).upper()
            stmt = select(Patient).where(
                Patient.mrn == mrn_str,
                Patient.clinician_id == clinician_id,
            )
            res = await self._session.execute(stmt)
            p = res.scalar_one_or_none()

            if p:
                return PatientResolutionResult(
                    status="RESOLVED",
                    patient=self._patient_service._to_read(p),
                )

        # Name Search
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
        matched: List[Patient] = []

        for p in all_patients:
            full_name = f"{p.first_name} {p.last_name}".lower()
            if (
                full_name in query_lower
                or p.first_name.lower() in query_lower
                or p.last_name.lower() in query_lower
            ):
                matched.append(p)

        # If no explicit name matched in query string:
        if not matched:
            # If clinician has exactly 1 patient, auto-resolve to that patient
            if len(all_patients) == 1:
                _log.info("PATIENT_RESOLVER.SINGLE_PATIENT_AUTO_RESOLVED", patient_id=all_patients[0].id)
                return PatientResolutionResult(
                    status="RESOLVED",
                    patient=self._patient_service._to_read(all_patients[0]),
                )
            
            # If multiple patients exist, return selectable candidate list
            candidates = [self._patient_service._to_read(m) for m in all_patients]
            return PatientResolutionResult(
                status="AMBIGUOUS",
                candidates=candidates,
                message=f"Please select which patient you would like to query ({len(candidates)} active patients found).",
            )

        if len(matched) == 1:
            return PatientResolutionResult(
                status="RESOLVED",
                patient=self._patient_service._to_read(matched[0]),
            )

        # Multiple patients match name -> AMBIGUOUS
        candidates = [self._patient_service._to_read(m) for m in matched]
        _log.info("PATIENT_RESOLVER.AMBIGUOUS", count=len(candidates))
        return PatientResolutionResult(
            status="AMBIGUOUS",
            candidates=candidates,
            message=f"Multiple patients match your query ({len(candidates)} candidates). Please select the correct patient.",
        )
