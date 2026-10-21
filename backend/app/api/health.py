"""Health check API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Health check",
    description="Returns service health status and version info",
    response_model=dict,
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Basic health check endpoint."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "version": "1.0.0",
        "service": "lumen-foundry",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "demo_mode": settings.DEMO_MODE and not settings.is_production,
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Kubernetes readiness probe endpoint",
    response_model=dict,
)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness check for container orchestration."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get(
    "/live",
    summary="Liveness probe",
    description="Kubernetes liveness probe endpoint",
    response_model=dict,
)
async def liveness_check() -> dict:
    """Liveness check for container orchestration."""
    return {"alive": True}