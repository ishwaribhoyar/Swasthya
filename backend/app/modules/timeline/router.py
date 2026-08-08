"""
Timeline API Router.

Endpoints:
  GET /timeline/patients/{patient_id}       — Rich longitudinal clinical encounters
  GET /timeline/patients/{patient_id}/stats — Timeline statistics header
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.timeline.schema import VisitGroupRead, TimelineStatsRead
from app.modules.timeline.service import TimelineService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/timeline", tags=["Timeline Intelligence"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.get(
    "/patients/{patient_id}",
    response_model=APIResponse[List[VisitGroupRead]],
    summary="Fetch rich longitudinal clinical encounters grouped by visit date",
)
async def get_patient_timeline(
    request: Request,
    patient_id: str,
    category: Optional[str] = Query(
        None,
        alias="doc_type",
        description="Filter by category: lab, prescription, vitals, note",
    ),
    search: Optional[str] = Query(
        None,
        description="Search clinical observations, medicines, or symptoms",
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[VisitGroupRead]]:
    """Fetch rich structured longitudinal timeline for a patient."""
    service = TimelineService(db)
    clinician_id = str(current_user["sub"])
    groups = await service.get_patient_timeline(patient_id, clinician_id, category, search)
    return APIResponse(
        success=True,
        message="Patient clinical timeline retrieved.",
        data=groups,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/stats",
    response_model=APIResponse[TimelineStatsRead],
    summary="Fetch longitudinal timeline statistics for the patient header",
)
async def get_patient_timeline_stats(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TimelineStatsRead]:
    """Fetch timeline statistics (total events, date range, category counts)."""
    service = TimelineService(db)
    clinician_id = str(current_user["sub"])
    stats = await service.get_timeline_stats(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Timeline statistics retrieved.",
        data=stats,
        request_id=_req_id(request),
    )
