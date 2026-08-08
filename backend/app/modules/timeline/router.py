"""
Timeline API Router.

Endpoints:
  GET /timeline/patients/{patient_id} — Fetch canonical longitudinal patient timeline grouped by visit date
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.timeline.schema import VisitGroupRead
from app.modules.timeline.service import TimelineService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/timeline", tags=["Timeline Intelligence"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.get(
    "/patients/{patient_id}",
    response_model=APIResponse[List[VisitGroupRead]],
    summary="Fetch canonical patient timeline grouped by visit date",
)
async def get_patient_timeline(
    request: Request,
    patient_id: str,
    category: Optional[str] = Query(None, description="Filter by event category: visit, lab_report, prescription, vitals, note"),
    search: Optional[str] = Query(None, description="Search term for medicines, labs, symptoms"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[VisitGroupRead]]:
    """Fetch longitudinal timeline events for a patient ordered by event_date."""
    service = TimelineService(db)
    clinician_id = str(current_user["sub"])
    groups = await service.get_patient_timeline(patient_id, clinician_id, category, search)
    return APIResponse(
        success=True,
        message="Patient timeline events retrieved.",
        data=groups,
        request_id=_req_id(request),
    )
