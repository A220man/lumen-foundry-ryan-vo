"""Pytest configuration for backend tests."""
from __future__ import annotations

import base64
import json
import time

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.config import settings
from app.main import create_app


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


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine):
    """Test client fixture."""
    from app.core.database import get_db
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient):
    """Test client with demo authentication."""
    token = create_demo_token(roles=["operator"])
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient):
    """Test client with admin authentication."""
    token = create_demo_token(roles=["admin"])
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client


@pytest_asyncio.fixture(autouse=True)
async def clean_db(test_engine):
    """Clean database before each test."""
    from app.models.model import Model as ModelDB
    from sqlalchemy import delete
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(delete(ModelDB))
        await session.commit()
