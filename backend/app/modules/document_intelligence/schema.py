"""
Pydantic schemas for the document_intelligence module.
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class Document_intelligenceBase(BaseModel):
    """Base schema."""
    model_config = ConfigDict(from_attributes=True)
    name: str

class Document_intelligenceCreate(Document_intelligenceBase):
    """Create schema."""
    pass

class Document_intelligenceRead(Document_intelligenceBase):
    """Read schema."""
    id: int
