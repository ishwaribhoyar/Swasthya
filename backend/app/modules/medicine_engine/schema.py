"""
Pydantic schemas for the medicine_engine module.
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class Medicine_engineBase(BaseModel):
    """Base schema."""
    model_config = ConfigDict(from_attributes=True)
    name: str

class Medicine_engineCreate(Medicine_engineBase):
    """Create schema."""
    pass

class Medicine_engineRead(Medicine_engineBase):
    """Read schema."""
    id: int
