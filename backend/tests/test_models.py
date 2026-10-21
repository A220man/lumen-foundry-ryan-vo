"""Models API tests."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

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


@pytest.mark.asyncio
async def test_list_models_empty(client: AsyncClient):
    """Test listing models when empty."""
    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_create_model(client: AsyncClient):
    """Test creating a model."""
    response = await client.post(
        "/api/v1/models",
        json={
            "name": "Test Model",
            "model_id": "test/model",
            "description": "A test model",
            "max_model_len": 4096,
            "default_temperature": 0.5,
            "default_max_tokens": 256,
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Model"
    assert data["model_id"] == "test/model"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_model_duplicate_model_id(client: AsyncClient):
    """Test creating duplicate model_id fails with 400."""
    await client.post(
        "/api/v1/models",
        json={"name": "Test Model", "model_id": "test/model"},
    )
    response = await client.post(
        "/api/v1/models",
        json={"name": "Test Model 2", "model_id": "test/model"},
    )
    assert response.status_code == 400  # Should return 400 for duplicate


@pytest.mark.asyncio
async def test_get_model(client: AsyncClient):
    """Test getting a model by ID."""
    create_resp = await client.post(
        "/api/v1/models",
        json={"name": "Test Model", "model_id": "test/model"},
    )
    model_id = create_resp.json()["id"]
    
    response = await client.get(f"/api/v1/models/{model_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["name"] == "Test Model"


@pytest.mark.asyncio
async def test_get_model_not_found(client: AsyncClient):
    """Test getting non-existent model."""
    response = await client.get("/api/v1/models/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_model(client: AsyncClient):
    """Test updating a model."""
    create_resp = await client.post(
        "/api/v1/models",
        json={"name": "Test Model", "model_id": "test/model"},
    )
    model_id = create_resp.json()["id"]
    
    response = await client.patch(
        f"/api/v1/models/{model_id}",
        json={"name": "Updated Model", "default_temperature": 0.9},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Model"
    assert data["default_temperature"] == 0.9


@pytest.mark.asyncio
async def test_delete_model(client: AsyncClient):
    """Test deleting a model."""
    create_resp = await client.post(
        "/api/v1/models",
        json={"name": "Test Model", "model_id": "test/model"},
    )
    model_id = create_resp.json()["id"]
    
    response = await client.delete(f"/api/v1/models/{model_id}")
    assert response.status_code == 204
    
    get_resp = await client.get(f"/api/v1/models/{model_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_list_models_pagination(client: AsyncClient):
    """Test model list pagination."""
    for i in range(5):
        await client.post(
            "/api/v1/models",
            json={"name": f"Model {i}", "model_id": f"test/model{i}"},
        )
    
    response = await client.get("/api/v1/models?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_list_models_active_only(client: AsyncClient):
    """Test filtering active models only."""
    await client.post("/api/v1/models", json={"name": "Active", "model_id": "active", "is_active": True})
    await client.post("/api/v1/models", json={"name": "Inactive", "model_id": "inactive", "is_active": False})
    
    response = await client.get("/api/v1/models?active_only=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Active"
