"""
Clinical Engine Repository.

Data access layer for lab_results, vital_signs, organ_scores, and clinical_alerts.
Enforces multi-tenant data isolation by clinician_id and patient_id.
"""
from __future__ import annotations

from typing import Sequence, Optional, List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clinical_engine.model import LabResult, VitalSign, OrganScore, ClinicalAlert


class ClinicalRepository:
    """Repository for clinical observations, scores, and alerts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ─── Lab Results ─────────────────────────────────────────────────────────

    async def save_lab_results(self, labs: List[LabResult]) -> None:
        for lab in labs:
            self._session.add(lab)
        await self._session.commit()

    async def list_labs_for_patient(
        self, patient_id: str, clinician_id: str, *, status: Optional[str] = None
    ) -> Sequence[LabResult]:
        query = select(LabResult).where(
            LabResult.patient_id == patient_id,
            LabResult.clinician_id == clinician_id,
        )
        if status:
            query = query.where(LabResult.status == status)
        query = query.order_by(LabResult.tested_at.desc())
        res = await self._session.execute(query)
        return res.scalars().all()

    # ─── Vital Signs ─────────────────────────────────────────────────────────

    async def save_vital_sign(self, vital: VitalSign) -> VitalSign:
        self._session.add(vital)
        await self._session.commit()
        await self._session.refresh(vital)
        return vital

    async def get_latest_vitals(self, patient_id: str, clinician_id: str) -> VitalSign | None:
        stmt = (
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id, VitalSign.clinician_id == clinician_id)
            .order_by(VitalSign.recorded_at.desc())
        )
        res = await self._session.execute(stmt)
        return res.scalars().first()

    async def list_vitals_for_patient(self, patient_id: str, clinician_id: str) -> Sequence[VitalSign]:
        stmt = (
            select(VitalSign)
            .where(VitalSign.patient_id == patient_id, VitalSign.clinician_id == clinician_id)
            .order_by(VitalSign.recorded_at.desc())
        )
        res = await self._session.execute(stmt)
        return res.scalars().all()

    # ─── Organ Scores ────────────────────────────────────────────────────────

    async def save_organ_scores(self, scores: List[OrganScore]) -> None:
        if scores:
            p_id = scores[0].patient_id
            c_id = scores[0].clinician_id
            stmt = delete(OrganScore).where(OrganScore.patient_id == p_id, OrganScore.clinician_id == c_id)
            await self._session.execute(stmt)
            for s in scores:
                self._session.add(s)
            await self._session.commit()

    async def get_latest_organ_scores(self, patient_id: str, clinician_id: str) -> Sequence[OrganScore]:
        stmt = (
            select(OrganScore)
            .where(OrganScore.patient_id == patient_id, OrganScore.clinician_id == clinician_id)
            .order_by(OrganScore.organ_system.asc())
        )
        res = await self._session.execute(stmt)
        return res.scalars().all()

    # ─── Clinical Alerts ──────────────────────────────────────────────────────

    async def save_alerts(self, alerts: List[ClinicalAlert]) -> None:
        if alerts:
            p_id = alerts[0].patient_id
            c_id = alerts[0].clinician_id
            # Delete previous unacknowledged alerts for this patient to prevent duplicate stale alert build-up
            stmt = delete(ClinicalAlert).where(
                ClinicalAlert.patient_id == p_id,
                ClinicalAlert.clinician_id == c_id,
                ClinicalAlert.is_acknowledged == False,
            )
            await self._session.execute(stmt)
            for a in alerts:
                self._session.add(a)
            await self._session.commit()

    async def list_alerts_for_patient(
        self, patient_id: str, clinician_id: str, *, severity: Optional[str] = None
    ) -> Sequence[ClinicalAlert]:
        query = select(ClinicalAlert).where(
            ClinicalAlert.patient_id == patient_id,
            ClinicalAlert.clinician_id == clinician_id,
        )
        if severity:
            query = query.where(ClinicalAlert.severity == severity)
        query = query.order_by(ClinicalAlert.created_at.desc())
        res = await self._session.execute(query)
        return res.scalars().all()

    async def acknowledge_alert(self, alert_id: str, clinician_id: str) -> ClinicalAlert | None:
        stmt = select(ClinicalAlert).where(
            ClinicalAlert.id == alert_id,
            ClinicalAlert.clinician_id == clinician_id,
        )
        res = await self._session.execute(stmt)
        alert = res.scalar_one_or_none()
        if alert:
            alert.is_acknowledged = True
            await self._session.commit()
            await self._session.refresh(alert)
        return alert
