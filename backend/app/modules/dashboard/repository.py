"""
Database repository for the dashboard module.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

class DashboardRepository:
    """CRUD operations for dashboard."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list:
        """Fetch all records."""
        return []
