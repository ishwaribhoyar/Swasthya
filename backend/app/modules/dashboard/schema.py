"""
Pydantic schemas for the dashboard module.
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class DashboardBase(BaseModel):
    """Base schema."""
    model_config = ConfigDict(from_attributes=True)
    name: str

class DashboardCreate(DashboardBase):
    """Create schema."""
    pass

class DashboardRead(DashboardBase):
    """Read schema."""
    id: int
