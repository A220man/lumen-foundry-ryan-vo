"""Core configuration using Pydantic Settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/lumen.db"
    
    # Keycloak / OIDC
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "lumen-foundry"
    KEYCLOAK_CLIENT_ID: str = "lumen-frontend"
    KEYCLOAK_CLIENT_SECRET: str = ""
    OIDC_DISCOVERY_URL: str = ""
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai-compatible"
    LLM_MODEL: str = ""
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    
    # Inference defaults
    MAX_MODEL_LEN: int = 8192
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 512
    
    # GPU monitoring
    ENABLE_GPU_MONITORING: bool = True
    
    # Demo mode (local-only, refuses in production)
    DEMO_MODE: bool = True
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def database_path(self) -> Path:
        if self.DATABASE_URL.startswith("sqlite"):
            path_str = self.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
            return Path(path_str)
        return Path("./data/lumen.db")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()