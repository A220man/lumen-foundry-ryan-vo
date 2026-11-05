"""Models API tests."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from app.models.model import Model as ModelDB


@pytest.mark.asyncio
async def test_list_models_empty(auth_client: AsyncClient):
    """Test listing models when empty."""
    response = await auth_client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_model(auth_client: AsyncClient):
    """Test creating a model."""
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
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Model"
    assert data["model_id"] == "test/model"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_model_duplicate_model_id(auth_client: AsyncClient):
    """Test creating duplicate model_id fails with 400."""
    await auth_client.post(
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
    response = await auth_client.post(
        "/api/v1/models",
        json={
            "name": "Test Model 2",
            "model_id": "test/model",
            "description": "Test description 2",
            "default_temperature": 0.7,
            "default_max_tokens": 100,
            "is_active": True,
        },
    )
    assert response.status_code == 400  # Should return 400 for duplicate


@pytest.mark.asyncio
async def test_get_model(auth_client: AsyncClient):
    """Test getting a model by ID."""
    create_resp = await auth_client.post(
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
    model_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/models/{model_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Model"


@pytest.mark.asyncio
async def test_get_model_not_found(auth_client: AsyncClient):
    """Test getting non-existent model."""
    response = await auth_client.get("/api/v1/models/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_model(auth_client: AsyncClient):
    """Test updating a model."""
    create_resp = await auth_client.post(
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
    model_id = create_resp.json()["id"]
    response = await auth_client.patch(
        f"/api/v1/models/{model_id}",
        json={
            "name": "Updated Model",
            "default_temperature": 0.9,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Model"
    assert data["default_temperature"] == 0.9


@pytest.mark.asyncio
async def test_delete_model(auth_client: AsyncClient):
    """Test deleting a model."""
    create_resp = await auth_client.post(
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
    model_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/models/{model_id}")
    assert response.status_code == 204
    get_resp = await auth_client.get(f"/api/v1/models/{model_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_models_pagination(auth_client: AsyncClient):
    """Test model list pagination."""
    for i in range(5):
        await auth_client.post(
            "/api/v1/models",
            json={
                "name": f"Model {i}",
                "model_id": f"test/model{i}",
                "description": f"Description {i}",
                "default_temperature": 0.7,
                "default_max_tokens": 100,
                "is_active": True,
            },
        )
    response = await auth_client.get("/api/v1/models?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_list_models_active_only(auth_client: AsyncClient):
    """Test filtering active models only."""
    await auth_client.post(
        "/api/v1/models",
        json={
            "name": "Active Model",
            "model_id": "test/active",
            "description": "Active",
            "default_temperature": 0.7,
            "default_max_tokens": 100,
            "is_active": True,
        },
    )
    await auth_client.post(
        "/api/v1/models",
        json={
            "name": "Inactive Model",
            "model_id": "test/inactive",
            "description": "Inactive",
            "default_temperature": 0.7,
            "default_max_tokens": 100,
            "is_active": False,
        },
    )
    response = await auth_client.get("/api/v1/models?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Active Model"
