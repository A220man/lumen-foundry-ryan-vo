"""Inference API endpoints - LLM inference and streaming."""
from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sse_starlette import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.model import Model as ModelDB
from app.core.config import settings


router = APIRouter(prefix="/inference", tags=["inference"])


class InferenceRequest(BaseModel):
    """Request model for inference."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int = Field(..., description="Registered model ID")
    prompt: str = Field(..., min_length=1, max_length=100000, description="Input prompt")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    stream: bool = Field(default=False, description="Stream response as SSE")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(None, ge=1)
    stop: Optional[list[str]] = Field(None, max_length=10)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)


class InferenceResponse(BaseModel):
    """Response model for non-streaming inference."""
    model_config = ConfigDict(protected_namespaces=())
    
    id: str
    model_id: int
    prompt: str
    generated_text: str
    finish_reason: str
    usage: dict
    created_at: float


class ModelMetrics(BaseModel):
    """Model performance metrics."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    avg_tokens_per_second: float
    gpu_memory_used_mb: Optional[float] = None
    gpu_utilization_percent: Optional[float] = None


# Mock inference engine for demo mode
class MockInferenceEngine:
    """Mock inference engine for demo/development."""
    
    def __init__(self):
        self.request_count = 0
        self.total_latency = 0.0
        self.total_tokens = 0
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate mock response as async generator."""
        self.request_count += 1
        start_time = time.time()
        
        # Simulate token generation
        mock_response = f"This is a mock response from Lumen Foundry for: '{prompt[:50]}...' "
        tokens = mock_response.split()
        
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.05)  # Simulate generation delay
            yield token + " "
        
        latency = (time.time() - start_time) * 1000
        self.total_latency += latency
        self.total_tokens += len(tokens)
    
    async def generate_sync(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Generate mock response synchronously."""
        self.request_count += 1
        start_time = time.time()
        
        mock_response = f"This is a mock response from Lumen Foundry for: '{prompt[:50]}...' "
        
        await asyncio.sleep(0.1)
        latency = (time.time() - start_time) * 1000
        self.total_latency += latency
        self.total_tokens += len(mock_response.split())
        
        return mock_response


mock_engine = MockInferenceEngine()


async def get_model_or_404(model_id: int, db: AsyncSession) -> ModelDB:
    """Get model by ID or raise 404."""
    model = await db.get(ModelDB, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if not model.is_active:
        raise HTTPException(status_code=400, detail="Model is not active")
    return model


@router.post(
    "",
    summary="Run inference",
    description="Run LLM inference (streaming or non-streaming)",
    response_model=InferenceResponse,
)
async def run_inference(
    request: InferenceRequest,
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
) -> InferenceResponse | EventSourceResponse:
    """Run inference on a registered model."""
    model = await get_model_or_404(request.model_id, db)
    
    # Use model defaults if not provided
    temperature = request.temperature if request.temperature is not None else model.default_temperature
    max_tokens = request.max_tokens if request.max_tokens is not None else model.default_max_tokens
    
    if request.stream:
        return await stream_inference(
            model=model,
            prompt=request.prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=request.top_p,
            top_k=request.top_k,
            stop=request.stop,
        )
    
    # Non-streaming inference
    start_time = time.time()
    generated = await mock_engine.generate_sync(
        prompt=request.prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    latency_ms = (time.time() - start_time) * 1000
    
    # Estimate token counts
    prompt_tokens = len(request.prompt.split())
    completion_tokens = len(generated.split())
    
    response = InferenceResponse(
        id=f"inf-{int(time.time() * 1000)}",
        model_id=model.id,
        prompt=request.prompt,
        generated_text=generated,
        finish_reason="stop",
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        created_at=start_time,
    )
    
    return response


async def stream_inference(
    model: ModelDB,
    prompt: str,
    temperature: float,
    max_tokens: int,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    stop: Optional[list[str]] = None,
) -> EventSourceResponse:
    """Stream inference response as SSE."""
    
    async def event_generator() -> AsyncGenerator[dict, None]:
        start_time = time.time()
        full_text = ""
        token_count = 0
        
        async for token in mock_engine.generate_stream(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            full_text += token
            token_count += 1
            
            yield {
                "event": "token",
                "data": json.dumps({
                    "token": token,
                    "token_count": token_count,
                }),
            }
        
        latency_ms = (time.time() - start_time) * 1000
        prompt_tokens = len(prompt.split())
        
        yield {
            "event": "done",
            "data": json.dumps({
                "finish_reason": "stop",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": token_count,
                    "total_tokens": prompt_tokens + token_count,
                },
                "latency_ms": latency_ms,
            }),
        }
    
    return EventSourceResponse(event_generator())


@router.get(
    "/models/{model_id}/metrics",
    summary="Get model metrics",
    description="Get performance metrics for a model",
    response_model=ModelMetrics,
)
async def get_model_metrics(
    model_id: int,
    db: AsyncSession = Depends(get_db),
) -> ModelMetrics:
    """Get model performance metrics."""
    model = await get_model_or_404(model_id, db)
    
    return ModelMetrics(
        model_id=model.id,
        total_requests=mock_engine.request_count,
        successful_requests=mock_engine.request_count,
        failed_requests=0,
        avg_latency_ms=mock_engine.total_latency / max(mock_engine.request_count, 1),
        avg_tokens_per_second=mock_engine.total_tokens / max(mock_engine.total_latency / 1000, 0.001),
    )


@router.get(
    "/stats",
    summary="Get global inference stats",
    description="Get global inference engine statistics",
    response_model=dict,
)
async def get_inference_stats() -> dict:
    """Get global inference statistics."""
    return {
        "total_requests": mock_engine.request_count,
        "total_tokens_generated": mock_engine.total_tokens,
        "avg_latency_ms": mock_engine.total_latency / max(mock_engine.request_count, 1),
        "uptime_seconds": time.time() - getattr(mock_engine, 'start_time', time.time()),
    }
