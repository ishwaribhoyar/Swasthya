"""
Timeline Repository — queries for canonical longitudinal timeline events.
"""
from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.timeline.model import TimelineEvent


class TimelineRepository:
    """Repository for TimelineEvent records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_event(self, event: TimelineEvent) -> TimelineEvent:
        """Create a timeline event record."""
        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def list_patient_events(
        self,
        patient_id: str,
        clinician_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Sequence[TimelineEvent]:
        """
        Fetch all timeline events for a patient ordered strictly by event_date DESC.
        """
        stmt = (
            select(TimelineEvent)
            .where(
                TimelineEvent.patient_id == patient_id,
                TimelineEvent.clinician_id == clinician_id,
            )
            .order_by(TimelineEvent.event_date.desc())
        )
        if category:
            stmt = stmt.where(TimelineEvent.event_type == category)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                (TimelineEvent.title.ilike(pattern))
                | (TimelineEvent.summary.ilike(pattern))
                | (TimelineEvent.entities_json.ilike(pattern))
            )

        res = await self._session.execute(stmt)
        return res.scalars().all()
