"""Models API endpoints - Model registry and management."""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model import Model as ModelDB


router = APIRouter(prefix="/models", tags=["models"])


class ModelCreate(BaseModel):
    """Request model for creating a model entry."""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., min_length=1, max_length=255, description="Model display name")
    model_id: str = Field(..., min_length=1, max_length=255, description="HuggingFace model ID or local path")
    description: str | None = Field(None, max_length=1000)
    max_model_len: int = Field(default=8192, ge=1, le=1048576)
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=512, ge=1, le=32768)
    is_active: bool = True


class ModelUpdate(BaseModel):
    """Request model for updating a model entry."""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    max_model_len: int | None = Field(None, ge=1, le=1048576)
    default_temperature: float | None = Field(None, ge=0.0, le=2.0)
    default_max_tokens: int | None = Field(None, ge=1, le=32768)
    is_active: bool | None = None


class ModelResponse(BaseModel):
    """Response model for model entries."""
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)
    
    id: int
    name: str
    model_id: str
    description: str | None
    max_model_len: int
    default_temperature: float
    default_max_tokens: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    """Paginated model list response."""
    items: list[ModelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get(
    "",
    summary="List models",
    description="Get paginated list of registered models",
    response_model=ModelListResponse,
)
async def list_models(
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
) -> ModelListResponse:
    """List registered models with pagination."""
    query = select(ModelDB)
    if active_only:
        query = query.where(ModelDB.is_active == True)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Apply pagination
    query = query.order_by(ModelDB.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    models = result.scalars().all()
    
    total_pages = (total + page_size - 1) // page_size
    
    return ModelListResponse(
        items=[ModelResponse.model_validate(m) for m in models],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    summary="Create model",
    description="Register a new model in the registry",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_model(
    model_data: ModelCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    """Create a new model entry."""
    model = ModelDB(
        name=model_data.name,
        model_id=model_data.model_id,
        description=model_data.description,
        max_model_len=model_data.max_model_len,
        default_temperature=model_data.default_temperature,
        default_max_tokens=model_data.default_max_tokens,
        is_active=model_data.is_active,
    )
    db.add(model)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Model ID already exists")
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.get(
    "/{model_id}",
    summary="Get model",
    description="Get model details by ID",
    response_model=ModelResponse,
)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    """Get a model by ID."""
    model = await db.get(ModelDB, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse.model_validate(model)


@router.patch(
    "/{model_id}",
    summary="Update model",
    description="Update model configuration",
    response_model=ModelResponse,
)
async def update_model(
    model_id: int,
    model_data: ModelUpdate,
    db: AsyncSession = Depends(get_db),
) -> ModelResponse:
    """Update a model entry."""
    model = await db.get(ModelDB, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    update_data = model_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Model ID already exists")
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete(
    "/{model_id}",
    summary="Delete model",
    description="Delete a model from the registry",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a model entry."""
    model = await db.get(ModelDB, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
