"""
Timeline Service Engine — compiles and groups timeline events by visit date.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.timeline.repository import TimelineRepository
from app.modules.timeline.schema import TimelineEventRead, VisitGroupRead
from app.observability.logger import get_logger

_log = get_logger(__name__)


class TimelineService:
    """Service compiling longitudinal patient event timelines."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TimelineRepository(session)

    async def get_patient_timeline(
        self,
        patient_id: str,
        clinician_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[VisitGroupRead]:
        """
        Fetch patient events ordered by event_date and group records from the same visit date.
        """
        events = await self._repo.list_patient_events(patient_id, clinician_id, category, search)

        # Group by YYYY-MM-DD event date
        grouped: Dict[str, List[TimelineEventRead]] = {}
        for ev in events:
            ev_read = TimelineEventRead.model_validate(ev)
            date_key = ev.event_date.strftime("%Y-%m-%d") if ev.event_date else "Unknown Date"
            if date_key not in grouped:
                grouped[date_key] = []
            grouped[date_key].append(ev_read)

        visit_groups: List[VisitGroupRead] = []
        for d_str, ev_list in grouped.items():
            cats = list(set(e.event_type for e in ev_list))
            dt_obj = ev_list[0].event_date if ev_list else None
            disp_date = dt_obj.strftime("%d %b %Y") if dt_obj else d_str

            visit_groups.append(
                VisitGroupRead(
                    visit_date=d_str,
                    display_date=disp_date,
                    event_count=len(ev_list),
                    categories=cats,
                    events=ev_list,
                )
            )

        _log.info(
            "TIMELINE.LOADED",
            patient_id=patient_id,
            total_events=len(events),
            visit_groups=len(visit_groups),
        )

        return visit_groups
