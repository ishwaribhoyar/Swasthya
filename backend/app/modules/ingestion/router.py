"""
Ingestion API router.

Endpoints:
  POST   /ingestion/patients/{patient_id}/upload — Multi-document upload (Up to 10 files)
  GET    /ingestion/patients/{patient_id}/documents — List patient documents
  GET    /ingestion/documents/{document_id} — Get document details & extracted text/HTML
  GET    /ingestion/documents/{document_id}/timeline — Get step-by-step pipeline execution logs
  DELETE /ingestion/documents/{document_id} — Delete document
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.ingestion.schema import (
    BatchUploadSummary,
    DocumentListItem,
    DocumentRead,
    ProcessingLogRead,
    TextEntryRequest,
)

from app.modules.ingestion.service import IngestionService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/ingestion", tags=["Ingestion & Document Intelligence"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.post(
    "/patients/{patient_id}/upload",
    response_model=APIResponse[BatchUploadSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Upload up to 10 medical documents simultaneously",
)
async def upload_documents(
    request: Request,
    patient_id: str,
    files: List[UploadFile] = File(..., description="Up to 10 medical PDFs or Images"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchUploadSummary]:
    """
    Ingest multiple medical documents into the asynchronous processing pipeline.
    Renders real-time extraction results, SHA256 duplicate status, and batch summary metrics.
    """
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    summary = await service.process_batch_upload(patient_id, clinician_id, files)
    return APIResponse(
        success=True,
        message="Batch upload processed successfully.",
        data=summary,
        request_id=_req_id(request),
    )


@router.post(
    "/patients/{patient_id}/text-entry",
    response_model=APIResponse[DocumentRead],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest direct copy-pasted clinical text or consultation note",
)
async def create_text_entry(
    request: Request,
    patient_id: str,
    entry_req: TextEntryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentRead]:
    """Ingest copy-pasted clinical text entry or transcribed consultation notes."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    doc = await service.process_text_entry(patient_id, clinician_id, entry_req)
    return APIResponse(
        success=True,
        message="Clinical text entry ingested successfully.",
        data=doc,
        request_id=_req_id(request),
    )



@router.get(
    "/patients/{patient_id}/documents",
    response_model=APIResponse[List[DocumentListItem]],
    summary="List patient medical documents",
)
async def list_documents(
    request: Request,
    patient_id: str,
    search: Optional[str] = Query(None, description="Search by filename or content"),
    category: Optional[str] = Query(None, description="Filter by category (lab, prescription, vitals, note, summary)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (completed, failed, duplicate)"),
    sort_by: str = Query("newest", description="Sort by: newest, oldest, filename, processing_time"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[DocumentListItem]]:
    """List medical documents for patient with filters and search."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    docs = await service.list_patient_documents(
        patient_id, clinician_id, search=search, category=category, status=status_filter, sort_by=sort_by
    )
    return APIResponse(
        success=True,
        message="Patient documents retrieved.",
        data=docs,
        request_id=_req_id(request),
    )


@router.get(
    "/documents/{document_id}",
    response_model=APIResponse[DocumentRead],
    summary="Get document details & extracted text/HTML",
)
async def get_document(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentRead]:
    """Fetch full document details, parse source, confidence score, and extracted text/HTML."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    doc = await service.get_document(document_id, clinician_id)
    return APIResponse(
        success=True,
        message="Document details retrieved.",
        data=doc,
        request_id=_req_id(request),
    )


@router.get(
    "/documents/{document_id}/timeline",
    response_model=APIResponse[List[ProcessingLogRead]],
    summary="Get step-by-step pipeline processing timeline logs",
)
async def get_document_timeline(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ProcessingLogRead]]:
    """Fetch pipeline execution logs for visual processing timeline modal."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    logs = await service.get_document_timeline(document_id, clinician_id)
    return APIResponse(
        success=True,
        message="Document processing timeline retrieved.",
        data=logs,
        request_id=_req_id(request),
    )


@router.post(
    "/documents/{document_id}/retry",
    response_model=APIResponse[DocumentRead],
    summary="Retry processing a failed document",
)
async def retry_document(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DocumentRead]:
    """Re-process a document that previously failed ingestion."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    doc = await service.retry_document(document_id, clinician_id)
    return APIResponse(
        success=True,
        message="Document queued for reprocessing.",
        data=doc,
        request_id=_req_id(request),
    )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete medical document",
)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a medical document."""
    service = IngestionService(db)
    clinician_id = str(current_user["sub"])
    await service.delete_document(document_id, clinician_id)
    return None
