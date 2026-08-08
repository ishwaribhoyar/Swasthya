"""
Patient repository — all SQLAlchemy database access for the patients module.
All queries are strictly scoped to the requesting clinician (`clinician_id`).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Sequence, Optional

from sqlalchemy import select, func, or_, and_, case, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.model import Patient
from app.modules.ingestion.model import Document
from app.modules.clinical_engine.model import ClinicalAlert


def calculate_age(dob: date) -> int:
    """Calculate age from Date of Birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class PatientRepository:
    """
    Data-access layer for Patient records.
    Enforces strict multi-tenant isolation by clinician_id.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, patient: Patient) -> Patient:
        """Persist a new Patient row and return it."""
        self._session.add(patient)
        await self._session.commit()
        await self._session.refresh(patient)
        return patient

    async def get_by_id(self, patient_id: str, clinician_id: str) -> Patient | None:
        """
        Return the Patient with the given UUID owned by clinician_id.
        Allows retrieving archived patients so detail view can render them.
        """
        stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinician_id == clinician_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

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
    ) -> tuple[Sequence[Patient], int]:
        """
        List patients owned by clinician_id with search, filters, sorting, and pagination.
        Includes last_document_at and risk_status computed via subqueries.
        """
        limit = min(limit, 200)

        query = select(Patient).where(Patient.clinician_id == clinician_id)

        if not include_archived:
            query = query.where(Patient.is_active == True)

        if gender:
            query = query.where(Patient.gender == gender)

        if blood_group:
            query = query.where(Patient.blood_group == blood_group)

        if search:
            term = f"%{search.lower()}%"
            query = query.where(
                or_(
                    func.lower(Patient.first_name).like(term),
                    func.lower(Patient.last_name).like(term),
                    func.lower(Patient.mrn).like(term),
                    func.lower(Patient.phone).like(term),
                    func.lower(Patient.email).like(term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(query.subquery())
        count_res = await self._session.execute(count_stmt)
        total = count_res.scalar_one()

        # Sorting
        if sort_by == "oldest":
            query = query.order_by(Patient.created_at.asc())
        elif sort_by == "first_name":
            query = query.order_by(Patient.first_name.asc())
        elif sort_by == "last_name":
            query = query.order_by(Patient.last_name.asc())
        elif sort_by == "mrn":
            query = query.order_by(Patient.mrn.asc())
        elif sort_by == "updated_at":
            query = query.order_by(Patient.updated_at.desc())
        else:  # newest (default)
            query = query.order_by(Patient.created_at.desc())

        # Pagination
        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        patients = list(result.scalars().all())

        if not patients:
            return patients, total

        patient_ids = [p.id for p in patients]

        # Subquery: last document upload date per patient
        doc_sq = (
            select(Document.patient_id, func.max(Document.created_at).label("last_doc"))
            .where(Document.patient_id.in_(patient_ids), Document.clinician_id == clinician_id)
            .group_by(Document.patient_id)
        )
        doc_res = await self._session.execute(doc_sq)
        last_doc_map = {row.patient_id: row.last_doc for row in doc_res.all()}

        # Subquery: max unacknowledged alert severity per patient
        SEVERITY_ORDER = {"CRITICAL": 3, "HIGH": 2, "MODERATE": 1, "LOW": 0, "NORMAL": 0}
        alert_sq = (
            select(ClinicalAlert.patient_id, ClinicalAlert.severity)
            .where(
                ClinicalAlert.patient_id.in_(patient_ids),
                ClinicalAlert.clinician_id == clinician_id,
                ClinicalAlert.is_acknowledged == False,
            )
        )
        alert_res = await self._session.execute(alert_sq)
        # Pick the highest severity per patient
        risk_map: dict[str, str] = {}
        for row in alert_res.all():
            pid, sev = row.patient_id, row.severity
            current = risk_map.get(pid, "NORMAL")
            if SEVERITY_ORDER.get(sev, 0) > SEVERITY_ORDER.get(current, 0):
                risk_map[pid] = sev

        # Attach computed fields to patient objects
        for p in patients:
            p.last_document_at = last_doc_map.get(p.id)  # type: ignore[attr-defined]
            p.risk_status = risk_map.get(p.id, "NORMAL") if p.id in last_doc_map else None  # type: ignore[attr-defined]

        return patients, total

    async def update(self, patient: Patient, updates: dict) -> Patient:
        """Apply field updates to patient and persist."""
        for field, value in updates.items():
            if value is not None and hasattr(patient, field):
                setattr(patient, field, value)
        await self._session.commit()
        await self._session.refresh(patient)
        return patient

    async def soft_delete(self, patient: Patient) -> Patient:
        """Mark patient as archived (soft delete)."""
        patient.is_active = False
        patient.archived_at = datetime.now(timezone.utc)
        await self._session.commit()
        await self._session.refresh(patient)
        return patient

    async def restore(self, patient: Patient) -> Patient:
        """Restore an archived patient."""
        patient.is_active = True
        patient.archived_at = None
        await self._session.commit()
        await self._session.refresh(patient)
        return patient

    async def get_statistics(self, clinician_id: str) -> dict:
        """
        Calculate rich patient metrics and distributions for clinician_id.
        """
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        base = select(Patient).where(Patient.clinician_id == clinician_id)
        result = await self._session.execute(base)
        patients = result.scalars().all()

        total = len(patients)
        active = sum(1 for p in patients if p.is_active)
        archived = total - active
        
        new_this_month = 0
        for p in patients:
            if p.created_at:
                c_at = p.created_at.replace(tzinfo=None)
                if c_at >= start_of_month:
                    new_this_month += 1

        gender_dist = {"male": 0, "female": 0, "other": 0}
        blood_dist: dict[str, int] = {}
        age_dist = {"0-18": 0, "19-35": 0, "36-50": 0, "51-65": 0, "65+": 0}

        for p in patients:
            if not p.is_active:
                continue
            # Gender
            if p.gender in gender_dist:
                gender_dist[p.gender] += 1
            # Blood Group
            if p.blood_group:
                blood_dist[p.blood_group] = blood_dist.get(p.blood_group, 0) + 1
            # Age Group
            age = calculate_age(p.date_of_birth)
            if age <= 18:
                age_dist["0-18"] += 1
            elif age <= 35:
                age_dist["19-35"] += 1
            elif age <= 50:
                age_dist["36-50"] += 1
            elif age <= 65:
                age_dist["51-65"] += 1
            else:
                age_dist["65+"] += 1

        return {
            "total_patients": total,
            "active_patients": active,
            "archived_patients": archived,
            "new_this_month": new_this_month,
            "gender_distribution": gender_dist,
            "blood_group_distribution": blood_dist,
            "age_distribution": age_dist,
        }
