"""
Router for the document_intelligence module.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/document_intelligence", tags=["Document_intelligence"])

@router.get("/", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_document_intelligence_list() -> dict:
    """Placeholder route."""
    raise HTTPException(status_code=501, detail="Not Implemented")
