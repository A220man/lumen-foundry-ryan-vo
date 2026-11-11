# Changelog

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — 2026-11-11

### Added
- OIDC Keycloak authentication with demo mode (complete)
- JWT token validation and role-based access control
- Auth middleware protecting API endpoints
- Role-based protection for models and inference endpoints (admin/operator/viewer)
- Frontend auth store with persisted login state
- Login component with demo mode and Keycloak login
- Layout component with user info and logout
- PrivateRoute component with proper async auth initialization

### Fixed
- PrivateRoute race condition: await checkAuth() before marking auth as checked

### Tests
- Backend: 9 auth tests pass (token validation, role dependencies, expired tokens, RBAC)
- Frontend: Login and Layout component tests pass

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-21

### Added
- FastAPI backend with modular router architecture
- Health check endpoints (liveness, readiness, health)
- Model registry API with CRUD operations and pagination
- Streaming inference engine with SSE support
- Mock inference engine for demo mode
- Real-time performance metrics collection
- React 18 + TypeScript + Vite frontend
- Dashboard with live statistics
- Model management UI with create/read/update/delete
- Inference playground with streaming and parameter controls
- Keycloak OIDC authentication with realm import
- Demo mode with mock JWT authentication
- Docker Compose orchestration (backend, frontend, Keycloak, SQLite)
- Comprehensive test suite (12+ backend tests, 3+ frontend tests)
- CI/CD workflow with pytest, vitest, Docker builds
- MIT license and documentation

### Security
- OIDC authorization code flow with PKCE
- Realm-based RBAC (admin/operator/viewer)
- HttpOnly SameSite cookies for production sessions
- Demo mode restricted to localhost
- No hardcoded secrets or credentials
