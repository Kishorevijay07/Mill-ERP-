# Rice Mill ERP

Production-grade ERP for a rice mill that receives Government-supplied paddy,
mills it into two rice categories, performs quality checks, dispatches to
destinations, raises Government claims, and tracks payments — with end-to-end
traceability from **Government paddy → milling → rice → delivery → claim → payment**.

The product, domain, and engineering specifications live in [`docs/`](docs/) and are
the source of truth. Start with [`docs/PRODUCT.md`](docs/PRODUCT.md) and
[`docs/BUSINESS-FLOW.md`](docs/BUSINESS-FLOW.md).

> **Status: Phase 0 — foundation.** The monorepo, tooling, infrastructure, and
> operational endpoints are in place. Business modules are implemented from Stage 1
> onward per [`docs/PHASE-1-EXECUTION.md`](docs/PHASE-1-EXECUTION.md).

## Architecture

Modular monolith:

```
Browser → Next.js (frontend) → FastAPI (backend) → PostgreSQL
                                     ├── Redis
                                     └── S3-compatible object storage (MinIO in dev)
```

Business rules live in backend service/domain layers. The frontend never talks to
the database directly. Stock changes flow exclusively through inventory
transactions inside database transactions. See
[`docs/DECISIONS.md`](docs/DECISIONS.md) for architecture decision records.

## Repository layout

```
.
├── docs/                     # product / domain / engineering specs (source of truth)
├── backend/                  # FastAPI + SQLAlchemy 2.x + Alembic (uv-managed)
│   ├── app/
│   │   ├── core/             # config, logging, database
│   │   ├── api/v1/           # versioned router aggregation
│   │   ├── modules/          # feature modules (system/ = health & readiness)
│   │   └── shared/           # ORM Base + mixins
│   ├── migrations/           # Alembic
│   └── tests/                # pytest
├── frontend/                 # Next.js App Router + TS + Tailwind + TanStack + RHF/Zod
├── e2e/                      # Playwright end-to-end tests
├── .github/workflows/        # CI
├── docker-compose.yml        # local Postgres, Redis, MinIO, backend, frontend
└── .env.example
```

## Prerequisites

- Node.js 22+ and npm
- Python 3.11 and [`uv`](https://docs.astral.sh/uv/)
- Docker (for Postgres, Redis, MinIO)

## Getting started

```bash
# 1. Configuration
cp .env.example .env                      # edit values; generate a real SECRET_KEY

# 2. Infrastructure (Postgres, Redis, MinIO)
docker compose up -d postgres redis minio minio-init

# 3. Backend
cd backend
uv sync --extra dev
uv run alembic upgrade head               # applies the auth schema (roles, users, sessions)

# Seed system roles and create the first admin (password is prompted or read
# from ADMIN_PASSWORD; never passed on the command line):
uv run python -m app.cli create-admin \
    --email admin@example.com --username admin --full-name "Site Admin"

uv run uvicorn app.main:app --reload --port 8000

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev                               # http://localhost:3000
```

- Backend health: http://localhost:8000/health
- Backend readiness: http://localhost:8000/ready
- OpenAPI docs: http://localhost:8000/docs

### Auth API (Stage 1)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/auth/login` | `{identifier, password}` → sets HttpOnly session cookie |
| `POST` | `/api/v1/auth/logout` | Revokes the session and clears the cookie |
| `GET`  | `/api/v1/auth/me` | Current user with roles and effective permissions |

Roles: **ADMIN** (all permissions), **OWNER** (operations, approvals, billing,
payments), **STAFF** (day-to-day operations). Authorization is enforced
server-side via a permission guard on every protected endpoint.

## Quality gates

| Area     | Commands |
|----------|----------|
| Backend  | `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy` · `uv run pytest` |
| Frontend | `npm run typecheck` · `npm run lint` · `npm run format:check` · `npm run build` |
| E2E      | `cd e2e && npm ci && npx playwright test` (browsers: `npx playwright install`) |

CI runs all of the above plus a clean-database Alembic migration check
(`.github/workflows/ci.yml`).

## Security & integrity (enforced from the foundation)

- Server-side authorization on every protected endpoint (RBAC).
- Backend validation is authoritative; frontend validation is UX only.
- Money and quantities use `NUMERIC`/`Decimal` — never floating point.
- Stock never edited directly; every movement is an inventory transaction inside a
  database transaction, guarding against negative stock and double-spend.
- Safe, structured error responses — no stack traces or internals leak to clients.
- Secrets come from the environment and are validated at startup; nothing is committed.
