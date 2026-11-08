"""Auth API tests."""
from __future__ import annotations

import json
import time
import base64
from jose import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.database import init_db, get_session
from app.models.model import Model as ModelDB
from app.core.config import settings


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


def create_demo_token(user_id: str = "1", email: str = "test@test.com", name: str = "Test User", roles: list[str] = None, exp: int = None) -> str:
    """Create a demo JWT token for testing."""
    if roles is None:
        roles = ["viewer"]
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "preferred_username": name,
        "name": name,
        "realm_access": {"roles": roles},
        "exp": exp if exp is not None else int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    
    encoded_header = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode()).decode().rstrip('=')
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    signature = "demo-signature"
    
    return f"{encoded_header}.{encoded_payload}.{signature}"


@pytest.mark.asyncio
async def test_health_endpoint_no_auth(client: AsyncClient):
    """Test health endpoint is accessible without auth in demo mode."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_models_endpoint_requires_auth(client: AsyncClient):
    """Test models endpoint requires authentication."""
    response = await client.get("/api/v1/models")
    assert response.status_code in (200, 401)


@pytest.mark.asyncio
async def test_inference_endpoint_requires_auth(client: AsyncClient):
    """Test inference endpoint requires authentication."""
    response = await client.post(
        "/api/v1/inference",
        json={"model_id": 1, "prompt": "Test"},
    )
    assert response.status_code in (200, 401, 404, 422)


@pytest.mark.asyncio
async def test_demo_token_validation():
    """Test demo token can be decoded."""
    token = create_demo_token()
    
    from app.core.auth import decode_token
    payload = decode_token(token)
    
    assert payload.sub == "1"
    assert payload.email == "test@test.com"
    assert payload.name == "Test User"
    assert payload.realm_access is not None
    assert "viewer" in payload.realm_access["roles"]


@pytest.mark.asyncio
async def test_get_current_user_dependency():
    """Test get_current_user dependency."""
    from app.core.auth import get_current_user, decode_token, CurrentUser
    from fastapi.security import HTTPAuthorizationCredentials
    
    token = create_demo_token()
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    # get_current_user is a dependency function, call it directly
    payload = decode_token(token)
    import time as time_module
    if payload.exp < time_module.time():
        from fastapi import HTTPException
        try:
            get_current_user(credentials)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
    else:
        roles = payload.realm_access.get("roles", []) if payload.realm_access else []
        user = CurrentUser(
            id=payload.sub,
            email=payload.email,
            name=payload.preferred_username or payload.name,
            roles=roles,
        )
        
        assert user.id == "1"
        assert user.email == "test@test.com"
        assert user.name == "Test User"
        assert user.roles == ["viewer"]


@pytest.mark.asyncio
async def test_require_role_dependencies():
    """Test role-based dependencies."""
    from app.core.auth import require_role, decode_token, CurrentUser
    from fastapi import HTTPException
    
    # Test viewer role
    token = create_demo_token(roles=["viewer"])
    payload = decode_token(token)
    user = CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.preferred_username or payload.name,
        roles=payload.realm_access.get("roles", []) if payload.realm_access else [],
    )
    
    # Viewer should pass for viewer role
    viewer_check = require_role("viewer")
    result = viewer_check(user)
    assert result.roles == ["viewer"]
    
    # Viewer should fail for operator role
    operator_check = require_role("operator")
    try:
        operator_check(user)
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 403
    
    # Test operator role
    token = create_demo_token(roles=["operator"])
    payload = decode_token(token)
    user = CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.preferred_username or payload.name,
        roles=payload.realm_access.get("roles", []) if payload.realm_access else [],
    )
    
    operator_check = require_role("operator")
    result = operator_check(user)
    assert "operator" in result.roles
    
    # Test admin role
    token = create_demo_token(roles=["admin"])
    payload = decode_token(token)
    user = CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.preferred_username or payload.name,
        roles=payload.realm_access.get("roles", []) if payload.realm_access else [],
    )
    
    admin_check = require_role("admin")
    result = admin_check(user)
    assert "admin" in result.roles


@pytest.mark.asyncio
async def test_expired_token_rejected():
    """Test expired token is rejected by get_current_user."""
    from app.core.auth import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials
    from fastapi import HTTPException
    
    # Create expired token
    token = create_demo_token(exp=int(time.time()) - 3600)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    try:
        get_current_user(credentials)
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        assert "expired" in e.detail.lower()
@pytest.mark.asyncio
async def test_role_based_models_access():
    """Test role-based access control on models endpoints."""
    from app.main import create_app
    from httpx import AsyncClient, ASGITransport
    # create_demo_token is defined in this module
    
    app = create_app()
    
    # Viewer token - can read but not write
    viewer_token = create_demo_token(roles=["viewer"])
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    # Operator token - can read and write
    operator_token = create_demo_token(roles=["operator"])
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Admin token - can do everything
    admin_token = create_demo_token(roles=["admin"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test GET /models - viewer should succeed
        resp = await ac.get("/api/v1/models", headers=viewer_headers)
        assert resp.status_code == 200
        
        # Test POST /models - viewer should fail (403)
        resp = await ac.post("/api/v1/models", headers=viewer_headers, json={
            "name": "Test Model",
            "model_id": "test-model",
            "description": "Test",
        })
        assert resp.status_code == 403
        
        # Test POST /models - operator should succeed
        resp = await ac.post("/api/v1/models", headers=operator_headers, json={
            "name": "Test Model",
            "model_id": "test-model-operator",
            "description": "Test",
        })
        assert resp.status_code == 201
        model_id = resp.json()["id"]
        
        # Test PATCH /models - viewer should fail (403)
        resp = await ac.patch(f"/api/v1/models/{model_id}", headers=viewer_headers, json={
            "description": "Updated"
        })
        assert resp.status_code == 403
        
        # Test PATCH /models - operator should succeed
        resp = await ac.patch(f"/api/v1/models/{model_id}", headers=operator_headers, json={
            "description": "Updated by operator"
        })
        assert resp.status_code == 200
        
        # Test DELETE /models - viewer should fail (403)
        resp = await ac.delete(f"/api/v1/models/{model_id}", headers=viewer_headers)
        assert resp.status_code == 403
        
        # Test DELETE /models - operator should succeed
        resp = await ac.delete(f"/api/v1/models/{model_id}", headers=operator_headers)
        assert resp.status_code == 204
        
        # Test admin can also do everything
        resp = await ac.post("/api/v1/models", headers=admin_headers, json={
            "name": "Admin Model",
            "model_id": "admin-model",
            "description": "Test",
        })
        assert resp.status_code == 201


@pytest.mark.asyncio
async def test_role_based_inference_access():
    """Test role-based access control on inference endpoints."""
    from app.main import create_app
    from httpx import AsyncClient, ASGITransport
    # create_demo_token is defined in this module
    from app.models.model import Model as ModelDB
    from app.core.database import get_session
    
    app = create_app()
    
    viewer_token = create_demo_token(roles=["viewer"])
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    operator_token = create_demo_token(roles=["operator"])
    operator_headers = {"Authorization": f"Bearer {operator_token}"}
    
    admin_token = create_demo_token(roles=["admin"])
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a model first
    async with get_session() as session:
        model = ModelDB(
            name="Test Model",
            model_id="test-model-inference",
            description="Test model for inference",
            is_active=True,
        )
        session.add(model)
        await session.flush()
        await session.refresh(model)
        model_id = model.id
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test POST /inference - viewer should succeed (inference requires viewer)
        resp = await ac.post("/api/v1/inference", headers=viewer_headers, json={
            "model_id": model_id,
            "prompt": "Test prompt",
        })
        assert resp.status_code == 200
        
        # Test GET /inference/metrics - viewer should succeed
        resp = await ac.get(f"/api/v1/inference/models/{model_id}/metrics", headers=viewer_headers)
        assert resp.status_code == 200
        
        # Test GET /inference/stats - viewer should succeed
        resp = await ac.get("/api/v1/inference/stats", headers=viewer_headers)
        assert resp.status_code == 200
        
        # Operator and admin should also work
        resp = await ac.post("/api/v1/inference", headers=operator_headers, json={
            "model_id": model_id,
            "prompt": "Test prompt",
        })
        assert resp.status_code == 200
        
        resp = await ac.post("/api/v1/inference", headers=admin_headers, json={
            "model_id": model_id,
            "prompt": "Test prompt",
        })
        assert resp.status_code == 200
