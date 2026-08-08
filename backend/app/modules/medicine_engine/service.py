"""
Medicine Engine Business Logic Service.
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.medicine_engine.prescription_model import Prescription, PrescriptionMedicine
from app.modules.medicine_engine.schema import (
    PrescriptionRead,
    MedicineSummaryRead,
    MedicineHistoryRead,
    PrescriptionMedicineRead,
)


class MedicineService:
    """Service layer for querying and aggregating patient prescription/medicine history."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_patient_prescriptions(
        self, patient_id: str, clinician_id: str
    ) -> List[PrescriptionRead]:
        """Fetch all prescriptions for a patient, ordered by prescription_date descending."""
        stmt = (
            select(Prescription)
            .where(
                Prescription.patient_id == patient_id,
                Prescription.clinician_id == clinician_id,
            )
            .order_by(desc(Prescription.prescription_date))
        )
        res = await self._session.execute(stmt)
        prescriptions = res.scalars().unique().all()
        return [PrescriptionRead.model_validate(p) for p in prescriptions]

    async def get_medicine_summary(
        self, patient_id: str, clinician_id: str
    ) -> List[MedicineSummaryRead]:
        """Aggregate unique medicines prescribed to a patient with prescription counts and dates."""
        stmt = (
            select(PrescriptionMedicine)
            .where(
                PrescriptionMedicine.patient_id == patient_id,
                PrescriptionMedicine.clinician_id == clinician_id,
            )
            .order_by(desc(PrescriptionMedicine.created_at))
        )
        res = await self._session.execute(stmt)
        all_meds = res.scalars().all()

        # Group by canonical lowercase medicine_name
        grouped = {}
        for med in all_meds:
            norm_name = med.medicine_name.strip().title()
            if norm_name not in grouped:
                grouped[norm_name] = []
            grouped[norm_name].append(med)

        summary_list = []
        for name, items in grouped.items():
            # Items sorted descending by created_at
            latest = items[0]
            first = items[-1]
            summary_list.append(
                MedicineSummaryRead(
                    medicine_name=name,
                    times_prescribed=len(items),
                    first_prescribed_date=first.created_at,
                    latest_prescribed_date=latest.created_at,
                    latest_strength=latest.strength,
                    latest_dose=latest.dose,
                    latest_frequency=latest.frequency,
                    latest_route=latest.route,
                    status="ACTIVE",
                )
            )

        summary_list.sort(key=lambda x: x.latest_prescribed_date, reverse=True)
        return summary_list

    async def get_medicine_history(
        self, patient_id: str, clinician_id: str, medicine_name: str
    ) -> Optional[MedicineHistoryRead]:
        """Get chronological prescription history for a specific medicine."""
        stmt = (
            select(PrescriptionMedicine)
            .where(
                PrescriptionMedicine.patient_id == patient_id,
                PrescriptionMedicine.clinician_id == clinician_id,
                func.lower(PrescriptionMedicine.medicine_name) == medicine_name.strip().lower(),
            )
            .order_by(desc(PrescriptionMedicine.created_at))
        )
        res = await self._session.execute(stmt)
        items = res.scalars().all()

        if not items:
            return None

        events = [PrescriptionMedicineRead.model_validate(m) for m in items]
        return MedicineHistoryRead(
            medicine_name=items[0].medicine_name.title(),
            total_prescriptions=len(items),
            first_prescribed=items[-1].created_at,
            latest_prescribed=items[0].created_at,
            prescription_events=events,
        )
