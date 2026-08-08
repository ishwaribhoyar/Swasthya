"""
Analytics API Router.

Endpoints:
  GET /analytics/patients/{patient_id}/trends — Fetch chart-ready longitudinal trends & anomaly detection
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.analytics.schema import AnalyticsOverviewRead
from app.modules.analytics.service import AnalyticsService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["Trend Analytics & Risk Detection"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.get(
    "/patients/{patient_id}/trends",
    response_model=APIResponse[AnalyticsOverviewRead],
    summary="Fetch longitudinal parameter trends and anomaly alerts",
)
async def get_patient_trends(
    request: Request,
    patient_id: str,
    parameter_name: Optional[str] = Query(None, description="Filter by specific parameter name (e.g. HbA1c, Glucose, Systolic BP)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AnalyticsOverviewRead]:
    """Fetch longitudinal trend analytics & chart-ready data for a patient."""
    service = AnalyticsService(db)
    clinician_id = str(current_user["sub"])
    analytics = await service.get_patient_analytics(patient_id, clinician_id, parameter_name)
    return APIResponse(
        success=True,
        message="Patient longitudinal analytics retrieved.",
        data=analytics,
        request_id=_req_id(request),
    )
