# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton

## Roadmap

### skeleton — FastAPI/React skeleton with install instructions and tests

Status: done

Acceptance:
- FastAPI backend with /health endpoint runs
- React+Vite+TypeScript frontend builds and serves
- Docker compose with backend, frontend, Keycloak, SQLite
- Backend pytest tests pass
- Frontend npm build and tests pass
- README with install/run/test steps

Implementation: `backend/app/main.py`, `backend/app/api/health.py`, `backend/app/api/models.py`, `backend/app/api/inference.py`, `backend/tests/test_health.py`, `backend/tests/test_models.py`, `backend/tests/test_inference.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/components/Dashboard.tsx`, `frontend/src/components/Models.tsx`, `frontend/src/components/Inference.tsx`, `frontend/src/components/Login.tsx`, `frontend/src/components/Layout.tsx`, `frontend/src/stores/authStore.ts`, `frontend/Dockerfile`, `compose.yaml`, `README.md`, `pyproject.toml`, `LICENSE`, `CHANGELOG.md`, `.gitignore`, `.env.example`, `portfolio.json`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `backend/tests/test_models.py`, `backend/tests/test_inference.py`, `frontend/tests/App.test.tsx`, `frontend/tests/Dashboard.test.tsx`, `frontend/tests/Layout.test.tsx`, `frontend/tests/Login.test.tsx`

### auth — OIDC Keycloak authentication with demo mode

Status: planned

Acceptance:
- Keycloak realm import works
- Login/logout flow functional
- Demo mode binds localhost only
- Auth middleware protects API endpoints

### inference — LLM inference engine with model management

Status: planned

Acceptance:
- Model registry API
- Inference endpoint with streaming
- GPU memory monitoring
- Batch inference support

### dashboard — Developer dashboard with model monitoring

Status: planned

Acceptance:
- Real-time throughput charts from API
- Model selection and configuration
- Request/response inspection

