"""
Analytics Repository — persistence & retrieval for ParameterHistory records.
"""
from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.model import ParameterHistory


class AnalyticsRepository:
    """Repository for ParameterHistory records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_parameter_record(self, param: ParameterHistory) -> ParameterHistory:
        """Create a parameter measurement record."""
        self._session.add(param)
        await self._session.commit()
        await self._session.refresh(param)
        return param

    async def list_patient_parameters(
        self, patient_id: str, clinician_id: str, parameter_name: Optional[str] = None
    ) -> Sequence[ParameterHistory]:
        """
        Fetch historical parameter measurements ordered by event_date ASC.
        """
        stmt = (
            select(ParameterHistory)
            .where(
                ParameterHistory.patient_id == patient_id,
                ParameterHistory.clinician_id == clinician_id,
            )
            .order_by(ParameterHistory.event_date.asc())
        )
        if parameter_name:
            stmt = stmt.where(
                (ParameterHistory.parameter_name.ilike(f"%{parameter_name}%"))
                | (ParameterHistory.normalized_name.ilike(f"%{parameter_name}%"))
            )

        res = await self._session.execute(stmt)
        return res.scalars().all()
