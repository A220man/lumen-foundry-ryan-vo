"""Inference API tests."""
from __future__ import annotations

import json
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.database import init_db, get_session
from app.models.model import Model as ModelDB


@pytest.fixture
async def client():
    """Test client fixture."""
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_db():
    """Setup test database."""
    await init_db()
    yield
    async with get_session() as session:
        await session.execute(ModelDB.__table__.delete())
        await session.commit()


@pytest.fixture
async def test_model(client: AsyncClient):
    """Create a test model."""
    response = await client.post(
        "/api/v1/models",
        json={"name": "Test Model", "model_id": "test/model", "default_max_tokens": 100},
    )
    return response.json()


@pytest.mark.asyncio
async def test_inference_non_streaming(client: AsyncClient, test_model: dict):
    """Test non-streaming inference."""
    response = await client.post(
        "/api/v1/inference",
        json={
            "model_id": test_model["id"],
            "prompt": "Hello, world!",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["model_id"] == test_model["id"]
    assert data["prompt"] == "Hello, world!"
    assert "generated_text" in data
    assert "usage" in data
    assert data["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_inference_streaming_endpoint(client: AsyncClient, test_model: dict):
    """Test streaming inference endpoint returns correct content-type."""
    response = await client.post(
        "/api/v1/inference",
        json={
            "model_id": test_model["id"],
            "prompt": "Test streaming",
            "stream": True,
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_inference_model_not_found(client: AsyncClient):
    """Test inference with non-existent model."""
    response = await client.post(
        "/api/v1/inference",
        json={"model_id": 99999, "prompt": "Test"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_inference_inactive_model(client: AsyncClient):
    """Test inference with inactive model."""
    create_resp = await client.post(
        "/api/v1/models",
        json={"name": "Inactive Model", "model_id": "inactive/model", "is_active": False},
    )
    model_id = create_resp.json()["id"]
    
    response = await client.post(
        "/api/v1/inference",
        json={"model_id": model_id, "prompt": "Test"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_inference_validation(client: AsyncClient, test_model: dict):
    """Test inference input validation."""
    # Empty prompt
    response = await client.post(
        "/api/v1/inference",
        json={"model_id": test_model["id"], "prompt": ""},
    )
    assert response.status_code == 422
    
    # Invalid temperature
    response = await client.post(
        "/api/v1/inference",
        json={"model_id": test_model["id"], "prompt": "Test", "temperature": 3.0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_model_metrics(client: AsyncClient, test_model: dict):
    """Test model metrics endpoint."""
    # Make a request first
    await client.post(
        "/api/v1/inference",
        json={"model_id": test_model["id"], "prompt": "Test"},
    )
    
    response = await client.get(f"/api/v1/inference/models/{test_model['id']}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == test_model["id"]
    assert data["total_requests"] >= 1
    assert data["successful_requests"] >= 1
    assert "avg_latency_ms" in data


@pytest.mark.asyncio
async def test_global_stats(client: AsyncClient):
    """Test global inference stats."""
    response = await client.get("/api/v1/inference/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_tokens_generated" in data
    assert "avg_latency_ms" in data
