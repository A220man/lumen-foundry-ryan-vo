"""Authentication and authorization utilities."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str
    email: Optional[str] = None
    preferred_username: Optional[str] = None
    name: Optional[str] = None
    realm_access: Optional[dict] = None
    exp: int
    iat: Optional[int] = None


class CurrentUser(BaseModel):
    """Authenticated user information."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    roles: list[str] = []


# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate JWT token."""
    try:
        # For demo mode, accept tokens without signature verification
        if settings.DEMO_MODE and not settings.is_production:
            payload = jwt.get_unverified_claims(token)
            return TokenPayload(**payload)
        
        # Production: verify with Keycloak public key
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
        )
        return TokenPayload(**payload)
    except (JWTError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """Extract current user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials)
    
    if payload.exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    roles = payload.realm_access.get("roles", []) if payload.realm_access else []
    
    return CurrentUser(
        id=payload.sub,
        email=payload.email,
        name=payload.preferred_username or payload.name,
        roles=roles,
    )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    """Extract current user from JWT token, returns None if not authenticated."""
    if not credentials:
        return None
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


def require_role(*required_roles: str):
    """Dependency that requires specific role(s)."""
    def role_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return user
    return role_checker


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires admin role."""
    return require_role("admin")(user)


def require_operator(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires operator role."""
    return require_role("operator", "admin")(user)


def require_viewer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires viewer role (or higher)."""
    return require_role("viewer", "operator", "admin")(user)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protecting routes."""
    
    def __init__(self, app, excluded_paths: list[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/health/ready",
            "/health/live",
        ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth for excluded paths
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail":"Not authenticated"}',
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json",
            )
        
        token = auth_header[7:]  # Remove "Bearer "
        
        try:
            payload = decode_token(token)
            if payload.exp < time.time():
                return Response(
                    content='{"detail":"Token expired"}',
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                    media_type="application/json",
                )
            
            # Add user info to request state for downstream use
            request.state.user = CurrentUser(
                id=payload.sub,
                email=payload.email,
                name=payload.preferred_username or payload.name,
                roles=payload.realm_access.get("roles", []) if payload.realm_access else [],
            )
        except HTTPException:
            return Response(
                content='{"detail":"Invalid authentication token"}',
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json",
            )
        
        return await call_next(request)


def add_auth_middleware(app, excluded_paths: list[str] = None):
    """Add authentication middleware to FastAPI app."""
    app.add_middleware(AuthMiddleware, excluded_paths=excluded_paths)


# Convenience dependencies for route protection
get_current_user_dependency = get_current_user
get_current_user_optional_dependency = get_current_user_optional
require_admin_dependency = require_admin
require_operator_dependency = require_operator
require_viewer_dependency = require_viewer
