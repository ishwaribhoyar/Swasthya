"""
Application settings and configuration.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    """Main application settings."""
    APP_NAME: str = "ClinIQ"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., description="Secret key for JWT")
    DATABASE_URL: str = Field(..., description="Database connection string")
    SARVAM_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    CORS_ORIGINS: List[str] = ["*"]


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

def get_settings() -> Settings:
    """Return the application settings."""
    return Settings()
