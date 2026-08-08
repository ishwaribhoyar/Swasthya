"""
Patient API router.

Endpoints:
  POST   /patients             — Create new patient (Generates sequential MRN)
  GET    /patients             — List patients (search, filter, sort, paginate)
  GET    /patients/statistics  — Summary & clinical distribution statistics
  GET    /patients/{id}        — Get patient details
  PATCH  /patients/{id}        — Update patient details
  DELETE /patients/{id}        — Archive patient (soft delete)
  POST   /patients/{id}/restore — Restore archived patient

All routes wrap data in standard APIResponse envelope and isolate data by JWT clinician_id.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.patients.schema import (
    PatientCreate,
    PatientListItem,
    PatientRead,
    PatientStatisticsResponse,
    PatientUpdate,
)
from app.modules.patients.service import PatientService
from app.shared.schemas.common import APIResponse
from app.shared.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/patients", tags=["Patients"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.post(
    "",
    response_model=APIResponse[PatientRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
)
async def create_patient(
    request: Request,
    body: PatientCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientRead]:
    """Register a new patient with an auto-generated sequential MRN (MRN-YYYY-######)."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    patient = await service.create_patient(body, clinician_id=clinician_id)
    return APIResponse(
        success=True,
        message="Patient registered successfully.",
        data=patient,
        request_id=_req_id(request),
    )


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[PatientListItem]],
    summary="List all active/archived patients",
)
async def list_patients(
    request: Request,
    search: Optional[str] = Query(None, description="Search by name, MRN, phone, email"),
    gender: Optional[str] = Query(None, description="Filter by gender (male, female, other)"),
    blood_group: Optional[str] = Query(None, description="Filter by blood group (A+, O+, etc.)"),
    include_archived: bool = Query(False, description="Include archived patients in list"),
    sort_by: str = Query("newest", description="Sort order: newest, oldest, first_name, last_name, mrn, updated_at"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedResponse[PatientListItem]]:
    """Retrieve paginated list of patients owned by the requesting clinician."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    skip = (page - 1) * page_size
    items, total = await service.list_patients(
        clinician_id,
        search=search,
        gender=gender,
        blood_group=blood_group,
        include_archived=include_archived,
        sort_by=sort_by,
        skip=skip,
        limit=page_size,
    )
    paginated = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if total > 0 else 0,
    )
    return APIResponse(
        success=True,
        message="Patient list retrieved.",
        data=paginated,
        request_id=_req_id(request),
    )


@router.get(
    "/statistics",
    response_model=APIResponse[PatientStatisticsResponse],
    summary="Get patient statistics and distributions",
)
async def get_patient_statistics(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientStatisticsResponse]:
    """Return summary statistics and demographic distributions for clinician's patients."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    stats = await service.get_statistics(clinician_id)
    return APIResponse(
        success=True,
        message="Patient statistics retrieved.",
        data=stats,
        request_id=_req_id(request),
    )


@router.get(
    "/{patient_id}",
    response_model=APIResponse[PatientRead],
    summary="Get patient details by ID",
)
async def get_patient(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientRead]:
    """Fetch full details of a single patient record owned by requesting clinician."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    patient = await service.get_patient(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient details retrieved.",
        data=patient,
        request_id=_req_id(request),
    )


@router.patch(
    "/{patient_id}",
    response_model=APIResponse[PatientRead],
    summary="Update patient details",
)
async def update_patient(
    request: Request,
    patient_id: str,
    body: PatientUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientRead]:
    """Update fields of an existing patient owned by requesting clinician."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    updated = await service.update_patient(patient_id, clinician_id, body)
    return APIResponse(
        success=True,
        message="Patient updated successfully.",
        data=updated,
        request_id=_req_id(request),
    )


@router.delete(
    "/{patient_id}",
    response_model=APIResponse[PatientRead],
    summary="Archive patient (soft delete)",
)
async def archive_patient(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientRead]:
    """Archive a patient record (soft delete). Data is preserved."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    archived = await service.archive_patient(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient archived successfully.",
        data=archived,
        request_id=_req_id(request),
    )


@router.post(
    "/{patient_id}/restore",
    response_model=APIResponse[PatientRead],
    summary="Restore archived patient",
)
async def restore_patient(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PatientRead]:
    """Restore an archived patient record back to active status."""
    service = PatientService(db)
    clinician_id = str(current_user["sub"])
    restored = await service.restore_patient(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient restored successfully.",
        data=restored,
        request_id=_req_id(request),
    )
