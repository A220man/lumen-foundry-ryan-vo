"""Inference API tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.models.model import Model as ModelDB


@pytest.fixture
async def test_model(auth_client: AsyncClient):
    """Create a test model."""
    response = await auth_client.post(
        "/api/v1/models",
        json={
            "name": "Test Model",
            "model_id": "test/model",
            "description": "Test description",
            "default_temperature": 0.7,
            "default_max_tokens": 100,
            "is_active": True,
        },
    )
    return response.json()


@pytest.mark.asyncio
async def test_inference_non_streaming(auth_client: AsyncClient, test_model: dict):
    """Test non-streaming inference."""
    response = await auth_client.post(
        "/api/v1/inference",
        json={
            "model_id": test_model["id"],
            "prompt": "Test prompt",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "generated_text" in data
    assert "finish_reason" in data
    assert data["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_inference_streaming_endpoint(auth_client: AsyncClient, test_model: dict):
    """Test streaming inference endpoint returns correct content-type."""
    response = await auth_client.post(
        "/api/v1/inference",
        json={
            "model_id": test_model["id"],
            "prompt": "Test prompt",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": True,
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_inference_model_not_found(auth_client: AsyncClient):
    """Test inference with non-existent model."""
    response = await auth_client.post(
        "/api/v1/inference",
        json={
            "model_id": 99999,
            "prompt": "Test prompt",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_inference_inactive_model(auth_client: AsyncClient):
    """Test inference with inactive model."""
    create_resp = await auth_client.post(
        "/api/v1/models",
        json={
            "name": "Inactive Model",
            "model_id": "test/inactive",
            "description": "Inactive model",
            "default_temperature": 0.7,
            "default_max_tokens": 100,
            "is_active": False,
        },
    )
    model_id = create_resp.json()["id"]
    response = await auth_client.post(
        "/api/v1/inference",
        json={
            "model_id": model_id,
            "prompt": "Test prompt",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False,
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_inference_validation(auth_client: AsyncClient, test_model: dict):
    """Test inference input validation."""
    response = await auth_client.post(
        "/api/v1/inference",
        json={"model_id": test_model["id"], "prompt": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_model_metrics(auth_client: AsyncClient, test_model: dict):
    """Test model metrics endpoint."""
    await auth_client.post(
        "/api/v1/inference",
        json={
            "model_id": test_model["id"],
            "prompt": "Test",
            "temperature": 0.7,
            "max_tokens": 50,
            "stream": False,
        },
    )
    response = await auth_client.get(f"/api/v1/inference/models/{test_model['id']}/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "avg_latency_ms" in data


@pytest.mark.asyncio
async def test_global_stats(admin_client: AsyncClient):
    """Test global inference stats (requires admin)."""
    response = await admin_client.get("/api/v1/inference/stats")
    assert response.status_code == 200
    data = response.json()
    assert "avg_latency_ms" in data
