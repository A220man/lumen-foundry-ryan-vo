"""API router package."""
from __future__ import annotations

from app.api import health, models, inference

__all__ = ["health", "models", "inference"]