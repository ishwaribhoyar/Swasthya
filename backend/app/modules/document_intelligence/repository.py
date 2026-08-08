"""
Database repository for the document_intelligence module.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

class Document_intelligenceRepository:
    """CRUD operations for document_intelligence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list:
        """Fetch all records."""
        return []
