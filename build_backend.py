import os
import textwrap
from pathlib import Path

base_dir = Path(r'c:\Users\datta.000\Desktop\hackathon\backend')

def w(path_str, content):
    p = base_dir / path_str
    p.parent.mkdir(parents=True, exist_ok=True)
    if not content:
        content = f'\"\"\"\nModule docstring for {p.name}.\n\"\"\"\nfrom __future__ import annotations\n'
    else:
        content = textwrap.dedent(content).strip() + '\n'
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

w('pyproject.toml', '''
[project]
name = "cliniq"
version = "0.1.0"
description = "ClinIQ Backend"
readme = "README.md"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w('requirements.txt', '''
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
aiosqlite==0.20.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
structlog==24.1.0
python-multipart==0.0.9
''')

w('requirements-dev.txt', '''
pytest
pytest-asyncio
httpx
ruff
black
''')

w('.env.example', '''
APP_NAME=ClinIQ
VERSION=0.1.0
DEBUG=True
SECRET_KEY=supersecretkeyexample
DATABASE_URL=sqlite+aiosqlite:///./cliniq.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
''')

w('.gitignore', '''
__pycache__/
*.pyc
.env
venv/
env/
.pytest_cache/
''')

w('app/__init__.py', '')
w('app/core/__init__.py', '')
w('app/core/config/__init__.py', '')

w('app/core/config/settings.py', '''
"""
Application settings and configuration.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    """Main application settings."""
    APP_NAME: str = "ClinIQ"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., description="Secret key for JWT")
    DATABASE_URL: str = Field(..., description="Database connection string")
    CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    """Return the application settings."""
    return Settings()
''')

w('app/core/config/jwt.py', '''
"""
JWT configuration constants.
"""
from __future__ import annotations

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
''')

w('app/core/config/database.py', '''
"""
Database configuration helpers.
"""
from __future__ import annotations
from app.core.config.settings import get_settings

def get_database_url() -> str:
    """Get the configured database URL."""
    return get_settings().DATABASE_URL
''')

w('app/core/config/logging.py', '''
"""
Logging configuration using structlog.
"""
from __future__ import annotations
import structlog

def configure_logging() -> None:
    """Configure structlog for the application."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )
''')

w('app/core/config/features.py', '''
"""
Feature flags configuration.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class FeatureFlags:
    """Application feature flags."""
    enable_ai_copilot: bool = False
    enable_advanced_analytics: bool = False
''')

w('app/core/security.py', '''
"""
Security utilities for password hashing and JWTs.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.core.config.jwt import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.config.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_settings().SECRET_KEY, algorithm=ALGORITHM)
''')

w('app/core/exceptions.py', '''
"""
Custom exception hierarchy for ClinIQ.
"""
from __future__ import annotations

class ClinIQBaseException(Exception):
    """Base exception for all ClinIQ errors."""
    pass

class NotFoundError(ClinIQBaseException):
    """Resource not found."""
    pass

class UnauthorizedError(ClinIQBaseException):
    """Authentication failed or missing."""
    pass

class ForbiddenError(ClinIQBaseException):
    """Insufficient permissions."""
    pass

class ValidationError(ClinIQBaseException):
    """Data validation failed."""
    pass

class ConflictError(ClinIQBaseException):
    """Resource conflict."""
    pass

class InternalError(ClinIQBaseException):
    """Internal server error."""
    pass
''')

w('app/core/dependencies.py', '''
"""
FastAPI dependencies.
"""
from __future__ import annotations
from typing import AsyncGenerator, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.core.config.settings import get_settings, Settings
from app.core.exceptions import UnauthorizedError

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Inject database session."""
    async for session in get_db_session():
        yield session

async def get_current_user() -> dict[str, Any]:
    """Stub for getting the current user."""
    return {"id": 1, "username": "admin"}
''')

w('app/database/__init__.py', '')

w('app/database/base.py', '''
"""
SQLAlchemy declarative base and mixins.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

class TimestampMixin:
    """Mixin to add created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
''')

w('app/database/session.py', '''
"""
Database session management.
"""
from __future__ import annotations
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config.database import get_database_url

engine = create_async_engine(get_database_url(), echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    async with AsyncSessionLocal() as session:
        yield session
''')

w('app/database/init_db.py', '''
"""
Database initialization logic.
"""
from __future__ import annotations
from app.database.session import engine
from app.database.base import Base

async def init_db() -> None:
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
''')

w('app/database/mixins.py', '''
"""
Additional SQLAlchemy mixins.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String

class SoftDeleteMixin:
    """Mixin for soft deletion support."""
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

class AuditMixin:
    """Mixin for tracking who created or updated a record."""
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String, nullable=True)
''')

w('app/observability/__init__.py', '')

w('app/observability/logger.py', '''
"""
Logger instantiation.
"""
from __future__ import annotations
import structlog
from typing import Any

def get_logger(name: str) -> Any:
    """Get a structured logger bound to a module name."""
    return structlog.get_logger().bind(module=name)
''')

w('app/observability/metrics.py', '''
"""
Metrics tracking stubs.
"""
from __future__ import annotations

class Metrics:
    """Metrics recording stubs."""
    @staticmethod
    def record_request(endpoint: str) -> None:
        """Record an incoming request."""
        pass
        
    @staticmethod
    def record_error(endpoint: str, error_type: str) -> None:
        """Record an error."""
        pass
        
    @staticmethod
    def record_latency(endpoint: str, duration: float) -> None:
        """Record request latency."""
        pass
''')

w('app/observability/audit.py', '''
"""
Audit logging utilities.
"""
from __future__ import annotations
from app.observability.logger import get_logger

logger = get_logger(__name__)

class AuditLogger:
    """Audit logger for tracking user actions."""
    @staticmethod
    def log_action(user_id: str, action: str, resource: str, details: dict) -> None:
        """Log a user action."""
        logger.info("audit_log", user_id=user_id, action=action, resource=resource, details=details)
''')

w('app/shared/__init__.py', '')
w('app/shared/schemas/__init__.py', '')

w('app/shared/schemas/common.py', '''
"""
Common Pydantic schemas.
"""
from __future__ import annotations
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    data: T
    message: str = "Success"

class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    details: str | None = None

class HealthCheckResponse(BaseModel):
    """Health check response schema."""
    status: str
    version: str
    timestamp: str
''')

w('app/shared/schemas/pagination.py', '''
"""
Pagination schemas.
"""
from __future__ import annotations
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
''')

w('app/shared/utils/__init__.py', '')

w('app/shared/utils/helpers.py', '''
"""
General helper utilities.
"""
from __future__ import annotations
import uuid
import re
from datetime import datetime, timezone

def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

def generate_uuid() -> str:
    """Generate a string UUID."""
    return str(uuid.uuid4())

def slugify(text: str) -> str:
    """Convert text to a slugified string."""
    return re.sub(r'[^\\w\\-]', '', text.lower().replace(' ', '-'))

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length."""
    return text[:max_length] + '...' if len(text) > max_length else text
''')

w('app/shared/utils/constants.py', '''
"""
Shared constants.
"""
from __future__ import annotations

STATUS_OK = "OK"
STATUS_ERROR = "ERROR"

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

DATE_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S%z"
''')

w('app/shared/middlewares/__init__.py', '')

w('app/shared/middlewares/cors.py', '''
"""
CORS middleware configuration.
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config.settings import get_settings

def configure_cors(app: FastAPI) -> None:
    """Configure CORS for the FastAPI application."""
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
''')

w('app/shared/middlewares/error_handler.py', '''
"""
Global error handler middleware.
"""
from __future__ import annotations
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ClinIQBaseException
from app.observability.logger import get_logger

logger = get_logger(__name__)

async def global_error_handler(request: Request, exc: ClinIQBaseException) -> JSONResponse:
    """Handle custom application exceptions globally."""
    logger.error("app_error", error=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "details": str(exc)}
    )
''')

w('app/shared/middlewares/request_id.py', '''
"""
Request ID middleware.
"""
from __future__ import annotations
import uuid
from fastapi import Request
from typing import Callable, Awaitable
from starlette.responses import Response

async def request_id_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Add X-Request-ID header to responses."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
''')

# Now defining DDD modules
modules = ['auth', 'patients', 'ingestion', 'document_intelligence', 'clinical_engine', 'medicine_engine', 'timeline', 'analytics', 'ai_copilot', 'dashboard']
for mod in modules:
    base = f"app/modules/{mod}"
    w(f"{base}/__init__.py", f'"""\\nModule {mod}.\\n"""\\nfrom __future__ import annotations\\n')
    
    w(f"{base}/router.py", f'''
"""
Router for the {mod} module.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/{mod}", tags=["{mod.capitalize()}"])

@router.get("/", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def get_{mod}_list() -> dict:
    """Placeholder route."""
    raise HTTPException(status_code=501, detail="Not Implemented")
''')

    w(f"{base}/service.py", f'''
"""
Business logic service for the {mod} module.
"""
from __future__ import annotations

class {mod.capitalize()}Service:
    """Service class for {mod}."""
    
    async def process(self) -> None:
        """Placeholder method."""
        pass
''')

    w(f"{base}/repository.py", f'''
"""
Database repository for the {mod} module.
"""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession

class {mod.capitalize()}Repository:
    """CRUD operations for {mod}."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list:
        """Fetch all records."""
        return []
''')

    w(f"{base}/schema.py", f'''
"""
Pydantic schemas for the {mod} module.
"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict

class {mod.capitalize()}Base(BaseModel):
    """Base schema."""
    model_config = ConfigDict(from_attributes=True)
    name: str

class {mod.capitalize()}Create({mod.capitalize()}Base):
    """Create schema."""
    pass

class {mod.capitalize()}Read({mod.capitalize()}Base):
    """Read schema."""
    id: int
''')

    w(f"{base}/model.py", f'''
"""
SQLAlchemy model for the {mod} module.
"""
from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database.base import Base

class {mod.capitalize()}Model(Base):
    """Database model."""
    __tablename__ = "{mod}_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
''')

    w(f"{base}/constants.py", f'''
"""
Constants for the {mod} module.
"""
from __future__ import annotations

MAX_ITEMS = 100
''')

    w(f"{base}/exceptions.py", f'''
"""
Exceptions for the {mod} module.
"""
from __future__ import annotations
from app.core.exceptions import ClinIQBaseException

class {mod.capitalize()}Error(ClinIQBaseException):
    """Base exception for {mod}."""
    pass
''')

    w(f"{base}/tests/__init__.py", '')
    w(f"{base}/tests/test_{mod}.py", f'''
"""
Tests for the {mod} module.
"""
from __future__ import annotations

def test_placeholder() -> None:
    """Placeholder test."""
    assert True
''')

# Extras
extra_files = {
    'ingestion': ['upload_manager', 'queue_manager', 'workers', 'job_scheduler', 'progress_tracker'],
    'document_intelligence': ['parse/__init__', 'vision/__init__', 'fallback/__init__', 'medical_parser/__init__', 'normalizer/__init__', 'normalizer/normalizer', 'validator/__init__', 'validator/validator'],
    'clinical_engine': ['medical_parser', 'reference_ranges', 'organ_scoring', 'trend_engine', 'alert_engine', 'snapshot_engine'],
    'medicine_engine': ['medicine_parser', 'medicine_timeline', 'medicine_service', 'knowledge_base'],
    'analytics': ['trend_engine', 'statistics', 'risk_engine', 'chart_engine'],
    'ai_copilot': ['query_router', 'patient_lookup', 'intent_classifier', 'prompt_builder', 'response_formatter']
}
for mod, files in extra_files.items():
    for f in files:
        class_name = f.split('/')[-1].replace('_', ' ').title().replace(' ', '')
        w(f"app/modules/{mod}/{f}.py", f'''
"""
Extra component: {f} for {mod}.
"""
from __future__ import annotations

class {class_name}:
    """Implementation of {f}."""
    pass
''')

# AI folders
ai_folders = ['__init__', 'llm/__init__', 'langchain/__init__', 'prompts/__init__', 'retrievers/__init__', 'embeddings/__init__', 'vectorstore/__init__', 'guardrails/__init__', 'tools/__init__', 'memory/__init__']
for f in ai_folders:
    w(f"app/ai/{f}.py", '')

# Tests
test_folders = ['__init__', 'unit/__init__', 'integration/__init__', 'system/__init__']
for f in test_folders:
    w(f"tests/{f}.py", '')
    
w('tests/conftest.py', '''
"""
Pytest fixtures.
"""
from __future__ import annotations
import pytest

@pytest.fixture
def client():
    """Test client fixture stub."""
    pass

@pytest.fixture
def session():
    """Test DB session stub."""
    pass
''')

# Fixtures
fixtures = ['__init__', 'patients/__init__', 'labs/__init__', 'notes/__init__', 'prescriptions/__init__', 'vitals/__init__']
for f in fixtures:
    w(f"fixtures/{f}.py", '')

# Docs
docs = ['architecture/overview.md', 'database/schema.md', 'api/endpoints.md', 'sequence/auth_flow.md']
for d in docs:
    w(f"docs/{d}", f'# {d.split("/")[-1].replace(".md", "").capitalize()}\n\nPlaceholder content.')

w('app/api/__init__.py', '')
w('app/api/v1/__init__.py', '')
w('app/api/v1/router.py', '''
"""
Main API router aggregating all module routers.
"""
from __future__ import annotations
from fastapi import APIRouter

# Import all module routers
from app.modules.auth.router import router as auth_router
from app.modules.patients.router import router as patients_router
from app.modules.ingestion.router import router as ingestion_router
from app.modules.document_intelligence.router import router as doc_intel_router
from app.modules.clinical_engine.router import router as clinical_router
from app.modules.medicine_engine.router import router as medicine_router
from app.modules.timeline.router import router as timeline_router
from app.modules.analytics.router import router as analytics_router
from app.modules.ai_copilot.router import router as copilot_router
from app.modules.dashboard.router import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(patients_router)
api_router.include_router(ingestion_router)
api_router.include_router(doc_intel_router)
api_router.include_router(clinical_router)
api_router.include_router(medicine_router)
api_router.include_router(timeline_router)
api_router.include_router(analytics_router)
api_router.include_router(copilot_router)
api_router.include_router(dashboard_router)
''')

w('app/main.py', '''
"""
Main FastAPI application factory and entry point.
"""
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config.settings import get_settings
from app.shared.middlewares.cors import configure_cors
from app.shared.middlewares.error_handler import global_error_handler
from app.shared.middlewares.request_id import request_id_middleware
from app.core.exceptions import ClinIQBaseException
from app.shared.utils.helpers import utcnow

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup/shutdown events."""
    yield

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG, lifespan=lifespan)
    
    configure_cors(app)
    app.middleware("http")(request_id_middleware)
    app.add_exception_handler(ClinIQBaseException, global_error_handler)
    
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/api/v1/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": settings.VERSION, "timestamp": utcnow().isoformat()}
        
    return app

app = create_app()
''')

print('All files successfully created.')
