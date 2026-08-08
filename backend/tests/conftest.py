"""
Pytest fixtures for ClinIQ backend tests.
Uses an isolated in-memory SQLite database for testing.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.session import get_db_session
from app.core.dependencies import get_db
import app.modules.auth.model  # noqa: F401
import app.modules.patients.model  # noqa: F401
import app.modules.ingestion.model  # noqa: F401
import app.modules.clinical_engine.model  # noqa: F401
import app.modules.ai_copilot.model  # noqa: F401
import app.modules.timeline.model  # noqa: F401
import app.modules.analytics.model  # noqa: F401



from sqlalchemy import event

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

@event.listens_for(test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)



@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory database and session for a test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP async client with overridden database dependency."""
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    fastapi_app.dependency_overrides.clear()
