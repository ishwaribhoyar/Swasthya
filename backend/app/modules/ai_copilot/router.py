"""
AI Copilot API Router.

Endpoints:
  POST /ai-copilot/query — Run 12-Stage Production Clinical RAG Pipeline for a patient
  GET  /ai-copilot/patients/{patient_id}/history — Fetch patient AI chat audit history
"""
from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.modules.ai_copilot.schema import AIQueryRequest, AIQueryResponse
from app.modules.ai_copilot.service import AICopilotService
from app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/ai-copilot", tags=["AI Copilot & Clinical RAG"])


def _req_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


@router.post(
    "/query",
    response_model=APIResponse[AIQueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Run 12-Stage Production Clinical RAG Pipeline for a patient",
)
async def query_patient_rag(
    request: Request,
    body: AIQueryRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AIQueryResponse]:
    """
    Execute full Production Clinical RAG Pipeline:
    Patient Context Snapshot -> Semantic Chunking -> Dense (384d) + Sparse BM25 Search
    -> Reciprocal Rank Fusion (RRF) -> Cross-Encoder Reranking -> MMR Diversification
    -> Grounded GPT-5 Nano Reasoning -> Source Citations & SHA256 Audit Hash.
    """
    service = AICopilotService(db)
    clinician_id = str(current_user["sub"])
    res = await service.query_patient(body.patient_id, clinician_id, body.query)
    return APIResponse(
        success=True,
        message="Clinical reasoning completed successfully.",
        data=res,
        request_id=_req_id(request),
    )


@router.get(
    "/patients/{patient_id}/history",
    response_model=APIResponse[List[AIQueryResponse]],
    summary="Fetch AI Copilot query history & audit logs for a patient",
)
async def get_patient_chat_history(
    request: Request,
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[AIQueryResponse]]:
    """Fetch past clinical AI reasoning logs and source citations for patient."""
    service = AICopilotService(db)
    clinician_id = str(current_user["sub"])
    history = await service.get_patient_chat_history(patient_id, clinician_id)
    return APIResponse(
        success=True,
        message="Patient AI chat history retrieved.",
        data=history,
        request_id=_req_id(request),
    )
