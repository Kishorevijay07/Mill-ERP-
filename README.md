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

### Government receiving API (Stage 2)

Chain: **Agency → Allocation → Delivery Order → Government Load**. Every mutation
allocates a human-readable reference (`AL-`, `DO-`, `LD-…`), stamps the acting
user, and writes an audit entry — atomically.

| Method | Path | Permission |
|--------|------|-----------|
| `POST`/`GET` | `/api/v1/government-agencies` | `government.agency.manage` / `.view` |
| `POST`/`GET` | `/api/v1/allocations` | `government.allocation.manage` / `.view` |
| `POST`/`GET` | `/api/v1/delivery-orders` | `government.delivery_order.manage` / `.view` |
| `POST`/`GET` | `/api/v1/government-loads` | `government.load.create` / `.view` |
| `POST` | `/api/v1/government-loads/{id}/arrive` | `government.load.create` (DRAFT → ARRIVED) |

### Receiving: weighment → QC → accept (Stage 2b)

Completes the load state machine and produces the first paddy stock. Acceptance is
the **only** way paddy inventory is created — via an inventory transaction, never a
direct stock edit.

| Method | Path | Permission | Transition |
|--------|------|-----------|-----------|
| `POST` | `/api/v1/government-loads/{id}/weighments` | `receiving.weighment.record` | `ARRIVED → WEIGHED` (net = gross − tare) |
| `POST` | `/api/v1/government-loads/{id}/paddy-quality` | `receiving.paddy_quality.record` | `WEIGHED → QC_PENDING` |
| `POST` | `/api/v1/government-loads/{id}/accept` | `government.load.accept` | `QC_PENDING → ACCEPTED` (+ Paddy Lot `PL-…` + inventory receipt) |
| `POST` | `/api/v1/government-loads/{id}/reject` | `government.load.accept` | `QC_PENDING → REJECTED` |
| `GET` | `/api/v1/paddy-lots`, `/paddy-lots/{id}` | `paddy.stock.view` | lot + derived `available_kg` |

Full load lifecycle: `DRAFT → ARRIVED → WEIGHED → QC_PENDING → ACCEPTED | REJECTED`.
Every transition is an explicit action endpoint, never a generic status `PATCH`;
each runs in one transaction that stamps the actor and writes an audit entry.

### Milling & rice (Stage 3)

Paddy is consumed into rice, with the first stock **consumption** guarded against
overspend. Rice stock exists only after QC passes.

| Method | Path | Permission | Effect |
|--------|------|-----------|--------|
| `POST` | `/api/v1/milling-batches` | `milling.batch.create` | Create batch (`MB-…`, DRAFT) with paddy inputs |
| `POST` | `/api/v1/milling-batches/{id}/start` | `milling.batch.create` | `DRAFT → IN_PROGRESS`; **consumes paddy** (locks each lot, checks stock, posts negative movement) |
| `POST` | `/api/v1/milling-batches/{id}/productions` | `milling.batch.create` | Record rice production (`RP-…`) with two-category outputs; bag count = ⌊qty ÷ bag weight⌋ |
| `POST` | `/api/v1/milling-batches/{id}/complete` | `milling.batch.create` | `IN_PROGRESS → COMPLETED` |
| `POST` | `/api/v1/rice-quality/{id}/pass` | `rice.qc.approve` | `PENDING → PASSED`; creates Rice Lot (`RL-…`) + posts rice stock |
| `POST` | `/api/v1/rice-quality/{id}/fail` | `rice.qc.approve` | `PENDING → FAILED`; no lot, no stock |
| `GET` | `/api/v1/rice-lots`, `/rice-lots/{id}` | `rice.stock.view` | Rice lots with derived `available_kg` |

Milling batch: `DRAFT → IN_PROGRESS → COMPLETED`. Rice QC: `PENDING → PASSED | FAILED`.
A batch that would overspend a paddy lot is refused (`409 insufficient_stock`) with
stock left untouched; concurrent milling of the same lot is serialized by a row
lock so it cannot double-spend.

### Dispatch & delivery (Stage 4)

Rice leaves the mill and destination receipt is recorded. Dispatching is the rice
**stock-out**, guarded like paddy consumption.

| Method | Path | Permission | Effect |
|--------|------|-----------|--------|
| `POST` | `/api/v1/dispatches` | `dispatch.create` | Create dispatch (`DEL-…`, DRAFT) with rice-lot items |
| `POST` | `/api/v1/dispatches/{id}/prepare` | `dispatch.create` | `DRAFT → PREPARED` |
| `POST` | `/api/v1/dispatches/{id}/dispatch` | `dispatch.confirm` | `PREPARED → DISPATCHED`; **deducts rice stock** (locks each lot, checks, posts negative movement) |
| `POST` | `/api/v1/dispatches/{id}/delivery-receipt` | `dispatch.confirm` | Records receipt (`REC-…`), computes shortage/excess, `→ DELIVERED` |
| `GET` | `/api/v1/dispatches`, `/dispatches/{id}` | `dispatch.view` | Dispatch with items + receipt |
| `GET` | `/api/v1/delivery-receipts`, `/…/{id}` | `dispatch.view` | Delivery receipts |

Dispatch: `DRAFT → PREPARED → DISPATCHED → DELIVERED`. A dispatch that would exceed
available rice is refused (`409 insufficient_stock`), the stock-out happens exactly
once (status guard), and failed-QC rice can never be dispatched (it never becomes a
rice lot). Shortage = dispatched − received; excess = received − dispatched.

### Claims, payments & invoice (Stage 5)

The mill bills the government for delivered rice and tracks payment to PAID. Money
is `NUMERIC(14,2)` — never float; totals are always computed server-side.

| Method | Path | Permission | Effect |
|--------|------|-----------|--------|
| `GET`/`PUT` | `/api/v1/mill-settings` | `settings.view` / `.manage` | Mill profile |
| `GET`/`POST`/`PUT`/`DELETE` | `/api/v1/charge-rates` | `settings.view` / `.manage` | Configurable charge rates |
| `POST` | `/api/v1/government-claims` | `billing.create` | Create claim (`CLM-…`) from delivered receipts; auto-fills lines from active rates × delivered qty |
| `PUT` | `/api/v1/government-claims/{id}/lines` | `billing.create` | Edit lines (DRAFT); totals recomputed server-side |
| `POST` | `/api/v1/government-claims/{id}/submit` · `/approve` | `billing.submit` · `billing.approve` | `DRAFT→SUBMITTED→APPROVED` |
| `POST` | `/api/v1/government-claims/{id}/invoice` | `billing.create` | Generate the invoice **PDF** (fpdf2) → document id |
| `GET` | `/api/v1/documents/{id}/download` | `billing.view` | Download the stored invoice PDF |
| `POST` | `/api/v1/payments` | `payment.record` | Record payment (≤ outstanding); `→ PARTIALLY_PAID` / `PAID` |
| `GET` | `/api/v1/reports/dashboard` | `reports.view` | KPIs (paddy/rice stock, pending delivery, claims, paid, outstanding) |

Claim: `DRAFT → SUBMITTED → APPROVED → PARTIALLY_PAID → PAID`. A delivery receipt can
be claimed at most once (unique link → duplicate-claim prevention); a payment cannot
exceed the outstanding balance (`409 overpayment`); the final payment flips the claim
to PAID. Invoice PDFs are stored via a documents module (local disk in dev, S3 later).

### Frontend

Full responsive app (Next.js App Router): login + a guarded shell with Dashboard,
Government Loads, Setup, Paddy Stock, Milling, Rice QC/Stock, Dispatch, Delivery
Receipts, Claims & Payments (with invoice download), and Settings. Action buttons are
permission-gated client-side; the backend enforces every permission regardless.

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
