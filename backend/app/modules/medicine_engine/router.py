"""
Router for the medicine_engine module.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/medicine_engine", tags=["Medicine_engine"])

@router.get("/", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_medicine_engine_list() -> dict:
    """Placeholder route."""
    raise HTTPException(status_code=501, detail="Not Implemented")
