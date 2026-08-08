"""
Router for Medicine Engine API endpoints.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.medicine_engine.schema import (
    PrescriptionRead,
    MedicineSummaryRead,
    MedicineHistoryRead,
)
from app.modules.medicine_engine.service import MedicineService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/medicine-engine", tags=["Medicine Engine"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.get(
    "/patients/{patient_id}/prescriptions",
    response_model=APIResponse[List[PrescriptionRead]],
    summary="List all prescriptions for a patient",
)
async def list_prescriptions(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[PrescriptionRead]]:
    """List structured prescription records."""
    service = MedicineService(db)
    clinician_id = str(current_user["sub"])
    data = await service.get_patient_prescriptions(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient prescriptions retrieved.",
        data=data,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/medicines",
    response_model=APIResponse[List[MedicineSummaryRead]],
    summary="List aggregated patient medicines summary",
)
async def get_medicine_summary(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[MedicineSummaryRead]]:
    """Get unique medicines prescribed with total counts and latest details."""
    service = MedicineService(db)
    clinician_id = str(current_user["sub"])
    data = await service.get_medicine_summary(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient medicine summary retrieved.",
        data=data,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/medicines/history",
    response_model=APIResponse[MedicineHistoryRead],
    summary="Get history for a specific medicine",
)
async def get_medicine_history(
    request: Request,
    patient_id: str,
    name: str = Query(..., description="Medicine name (e.g., Metformin)"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[MedicineHistoryRead]:
    """Get prescription timeline for a single medicine."""
    service = MedicineService(db)
    clinician_id = str(current_user["sub"])
    data = await service.get_medicine_history(patient_id, clinician_id, name)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prescription history found for medicine '{name}'.",
        )
    return APIResponse(
        success=True,
        message=f"Medicine history for '{name}' retrieved.",
        data=data,
        request_id=_req_id(request),
    )
