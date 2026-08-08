"""
Patient service — business logic layer for patient management.

Handles sequential MRN allocation, clinician data scoping, structured audit events,
and conversion to Pydantic domain models.
"""
from __future__ import annotations

from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.modules.patients.model import Patient
from app.modules.patients.mrn_service import MRNSequenceService
from app.modules.patients.repository import PatientRepository, calculate_age
from app.modules.patients.schema import (
    PatientCreate,
    PatientListItem,
    PatientRead,
    PatientStatisticsResponse,
    PatientUpdate,
)
from app.observability.logger import get_logger

_log = get_logger(__name__)


class PatientService:
    """
    Business logic for patient management.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PatientRepository(session)
        self._mrn_service = MRNSequenceService(session)

    def _to_read(self, patient: Patient) -> PatientRead:
        """Convert Patient ORM model to PatientRead schema with calculated age."""
        return PatientRead(
            id=patient.id,
            clinician_id=patient.clinician_id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            age=calculate_age(patient.date_of_birth),
            gender=patient.gender,
            phone=patient.phone,
            email=patient.email,
            blood_group=patient.blood_group,
            emergency_contact_name=patient.emergency_contact_name,
            emergency_contact_phone=patient.emergency_contact_phone,
            address=patient.address,
            allergies=patient.allergies,
            chronic_conditions=patient.chronic_conditions,
            notes=patient.notes,
            is_active=patient.is_active,
            archived_at=patient.archived_at,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )

    def _to_list_item(self, patient: Patient) -> PatientListItem:
        """Convert Patient ORM model to PatientListItem schema."""
        return PatientListItem(
            id=patient.id,
            mrn=patient.mrn,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            age=calculate_age(patient.date_of_birth),
            gender=patient.gender,
            phone=patient.phone,
            blood_group=patient.blood_group,
            emergency_contact_name=patient.emergency_contact_name,
            is_active=patient.is_active,
            archived_at=patient.archived_at,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )

    async def create_patient(self, data: PatientCreate, clinician_id: str) -> PatientRead:
        """
        Register a new patient for the authenticated clinician.
        Generates a sequential MRN (MRN-YYYY-######).
        """
        mrn = await self._mrn_service.generate_next_mrn()

        patient = Patient(
            clinician_id=clinician_id,
            mrn=mrn,
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            email=data.email,
            blood_group=data.blood_group,
            emergency_contact_name=data.emergency_contact_name,
            emergency_contact_phone=data.emergency_contact_phone,
            address=data.address,
            allergies=data.allergies,
            chronic_conditions=data.chronic_conditions,
            notes=data.notes,
            created_by=clinician_id,
        )

        saved = await self._repo.create(patient)
        _log.info(
            "PATIENT.CREATED",
            patient_id=saved.id,
            clinician_id=clinician_id,
            mrn=saved.mrn,
        )
        return self._to_read(saved)

    async def get_patient(self, patient_id: str, clinician_id: str) -> PatientRead:
        """
        Retrieve a patient record owned by clinician_id.
        """
        patient = await self._repo.get_by_id(patient_id, clinician_id)
        if not patient:
            raise NotFoundError(f"Patient with ID '{patient_id}' was not found.")
        return self._to_read(patient)

    async def list_patients(
        self,
        clinician_id: str,
        *,
        search: Optional[str] = None,
        gender: Optional[str] = None,
        blood_group: Optional[str] = None,
        include_archived: bool = False,
        sort_by: str = "newest",
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PatientListItem], int]:
        """
        List active and optionally archived patients with search, filters, and pagination.
        """
        if search:
            _log.info("PATIENT.SEARCHED", clinician_id=clinician_id, query=search)

        patients, total = await self._repo.list_patients(
            clinician_id,
            search=search,
            gender=gender,
            blood_group=blood_group,
            include_archived=include_archived,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
        )
        items = [self._to_list_item(p) for p in patients]
        return items, total

    async def update_patient(
        self, patient_id: str, clinician_id: str, data: PatientUpdate
    ) -> PatientRead:
        """
        Update fields of an existing patient owned by clinician_id.
        """
        patient = await self._repo.get_by_id(patient_id, clinician_id)
        if not patient:
            raise NotFoundError(f"Patient with ID '{patient_id}' was not found.")

        updates = data.model_dump(exclude_unset=True)
        updated = await self._repo.update(patient, updates)
        _log.info(
            "PATIENT.UPDATED",
            patient_id=patient_id,
            clinician_id=clinician_id,
        )
        return self._to_read(updated)

    async def archive_patient(self, patient_id: str, clinician_id: str) -> PatientRead:
        """
        Archive (soft delete) a patient.
        """
        patient = await self._repo.get_by_id(patient_id, clinician_id)
        if not patient:
            raise NotFoundError(f"Patient with ID '{patient_id}' was not found.")

        archived = await self._repo.soft_delete(patient)
        _log.info(
            "PATIENT.ARCHIVED",
            patient_id=patient_id,
            clinician_id=clinician_id,
        )
        return self._to_read(archived)

    async def restore_patient(self, patient_id: str, clinician_id: str) -> PatientRead:
        """
        Restore an archived patient.
        """
        patient = await self._repo.get_by_id(patient_id, clinician_id)
        if not patient:
            raise NotFoundError(f"Patient with ID '{patient_id}' was not found.")

        restored = await self._repo.restore(patient)
        _log.info(
            "PATIENT.RESTORED",
            patient_id=patient_id,
            clinician_id=clinician_id,
        )
        return self._to_read(restored)

    async def get_statistics(self, clinician_id: str) -> PatientStatisticsResponse:
        """
        Return rich statistics for the clinician's patients.
        """
        stats = await self._repo.get_statistics(clinician_id)
        return PatientStatisticsResponse(**stats)
