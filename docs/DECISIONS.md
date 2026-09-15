# Architecture Decision Records

Chronological record of significant, hard-to-reverse decisions. Each entry states
context, the decision, and consequences. Supersede rather than rewrite history.

---

## ADR-0009 — Money as `NUMERIC(14,2)`, totals computed server-side

**Status:** Accepted (Stage 5)

**Context.** Claims/payments require exact currency arithmetic; floats are banned.

**Decision.** Monetary columns are `NUMERIC(14,2)`, rates `NUMERIC(14,4)`,
quantities `NUMERIC(14,3)`; all handling uses Python `Decimal` with explicit
`ROUND_HALF_UP` quantization. Gross/deduction/net and outstanding balances are
always recomputed server-side from the lines/payments — never trusted from the
client. Payments are capped at the outstanding balance.

**Consequences.** No floating-point drift; the API is the single source of truth
for money.

---

## ADR-0010 — Invoice PDFs via fpdf2

**Status:** Accepted (Stage 5)

**Context.** The mill must generate a government claim/invoice document. The docs
mention Playwright-based PDF, which is heavy (Chromium) for the backend image.

**Decision.** Render invoices with **fpdf2** — pure-Python, no native libraries —
so generation works on Windows dev and in a slim Docker image. Invoices are
generated from the claim + mill settings and stored as documents.

**Consequences.** Zero extra system dependencies; core fonts are latin-1 (currency
shown as code/"Rs."). A richer HTML→PDF renderer can be swapped in later behind the
same generation call.

---

## ADR-0011 — Documents: metadata in Postgres, bytes in object storage

**Status:** Accepted (Stage 5)

**Context.** DEVELOPMENT-RULES require file bytes in object storage with metadata
in Postgres. MinIO/S3 is not running in local dev.

**Decision.** A `documents` table holds metadata; a `Storage` protocol abstracts
byte storage with a `LocalDiskStorage` dev backend (base dir from settings) and an
S3 backend as the later swap. Storage keys are generated server-side; original
filenames are never used as paths.

**Consequences.** Invoices work immediately in dev without MinIO; production swaps
the storage backend without changing callers.

---

## ADR-0001 — Modular monolith with a versioned REST API

**Status:** Accepted (Phase 0)

**Context.** Phase 1 is a bounded operational workflow for a single mill. The specs
mandate a modular monolith and explicitly defer microservices.

**Decision.** A single FastAPI application organised into feature modules under
`app/modules/`, exposing a versioned REST API at `/api/v1`. Routers stay thin;
business logic lives in service/domain layers; persistence is isolated.

**Consequences.** Simple to develop, test, and deploy. Module boundaries keep a
future extraction path open without paying distributed-systems cost now.

---

## ADR-0002 — `uv` for backend dependency and environment management

**Status:** Accepted (Phase 0)

**Context.** Reproducible installs and fast CI matter; Poetry is not installed, `uv`
is available and fast.

**Decision.** Use `uv` with `pyproject.toml` and a committed `uv.lock`. Docker and CI
install with `uv sync --frozen`.

**Consequences.** Fast, deterministic installs. Contributors need `uv`
(single self-contained binary).

---

## ADR-0003 — UUID primary keys with separate human-readable reference numbers

**Status:** Accepted (Phase 0)

**Context.** DOMAIN-MODEL and DATABASE-SPEC require non-guessable IDs and
user-facing transaction references (AL-000001, LD-000001, …) that must not be
primary keys.

**Decision.** Core entities use UUID PKs (`app/shared/base_model.py`). Human-readable
references are separate, unique, indexed columns generated server-side (per-prefix
sequence, zero-padded) — implemented with the first business module in Stage 1.

**Consequences.** Stable internal identity; friendly external references; no
information leakage from sequential PKs.

---

## ADR-0004 — Inventory as append-only transactions; no direct stock edits

**Status:** Accepted (Phase 0)

**Context.** Traceability and financial integrity are the core invariants. Stock must
never be an editable number.

**Decision.** All stock changes are `inventory_transactions` rows written inside a
database transaction with row-level locking on the affected lot. Cached available
quantities, if introduced, are derived and protected by that transactional logic.
Never expose a UI or endpoint that edits available stock directly.

**Consequences.** Full movement history; prevents negative stock, double deduction,
and duplicate dispatch/claim/payment under concurrency. Slightly more write work per
operation — an accepted trade-off.

---

## ADR-0005 — HttpOnly cookie sessions for browser authentication

**Status:** Accepted (Phase 0) · Implemented (Stage 1)

**Context.** SECURITY.md prefers HttpOnly/Secure/SameSite cookies and warns against
storing tokens in localStorage.

**Decision.** Opaque, high-entropy session tokens carried in an HttpOnly, Secure
(staging/production), SameSite=Lax cookie. Only a SHA-256 hash of each token is
persisted, so a database disclosure yields no live session credential. RBAC
permissions are checked server-side on every protected endpoint
(`require_permission`). No JWT in the browser for Phase 1.

**Consequences.** Strong XSS posture; straightforward per-session revocation.
SameSite=Lax blocks cookies on cross-site POST, covering the common CSRF vector;
an explicit CSRF token is deferred and tracked as a hardening item.

---

## ADR-0007 — Database-backed sessions for Phase 1 (Redis deferred)

**Status:** Accepted (Stage 1) — refines ADR-0005

**Context.** ADR-0005 originally envisioned Redis-held session state. In practice
Phase-1 sessions must be durable, revocable, auditable, and — importantly —
testable without standing up extra infrastructure in every CI job.

**Decision.** Persist sessions in a `user_sessions` table (token hash, expiry,
revocation, user-agent/IP) in PostgreSQL. Redis remains provisioned for future
use (rate limiting, caching, higher-scale session lookup) but is not on the auth
critical path in Phase 1.

**Consequences.** Sessions survive restarts and are queryable/auditable; auth tests
run against the same database with no Redis dependency. Session validation is a
single indexed lookup — acceptable at Phase-1 scale; revisit if lookup volume
warrants moving hot session state to Redis.

---

## ADR-0008 — Dialect-agnostic `Uuid` column type

**Status:** Accepted (Stage 1) — refines ADR-0003

**Context.** Models used `postgresql.UUID`, which prevented running the ORM on
SQLite for fast, hermetic tests.

**Decision.** Use SQLAlchemy 2.0's portable `Uuid` type in the shared base mixin.
It renders as native `UUID` on PostgreSQL (production) and `CHAR(32)` on SQLite
(tests). Migrations use dialect-agnostic server defaults (`sa.func.now()`,
`sa.true()/false()`) so a single migration script runs on both backends; the CI
`migrations` job still executes it against real PostgreSQL.

**Consequences.** Integration tests run in-process on SQLite with no external
services; production identity semantics are unchanged.

---

## ADR-0006 — Explicit state-transition endpoints over generic status PATCH

**Status:** Accepted (Phase 0)

**Context.** Loads, batches, QC, dispatches, and claims have defined state machines
(BUSINESS-FLOW.md). Arbitrary status edits would bypass business rules.

**Decision.** Model transitions as explicit action endpoints (e.g.
`POST /government-loads/{id}/accept`) whose services enforce guards, write inventory
transactions where relevant, and record audit entries. No generic status PATCH.

**Consequences.** Business rules are centralised and enforceable; the API documents
the real workflow.

---

## Open decisions (require validation during implementation)

These follow the smallest safe Phase-1 interpretation permitted by the specs and are
flagged for confirmation with the product owner:

1. **Weighment cardinality** — `GovernmentLoad 1:N Weighment` with an `is_final`
   authoritative flag (DOMAIN-MODEL leaves this to the app). Simpler 1:1 is possible
   if re-weighing is never needed.
2. **Load → PaddyLot** and **ProductionOutput → RiceLot** — modelled **1:1** for
   Phase 1; the schema keeps 1:N possible without a breaking change.
3. **Dispatch → DeliveryReceipt** — one final receipt plus shortage/excess fields
   (no partial receipts in Phase 1).
4. **Government charge/rate model** — claim line rates are configuration
   (`mill_settings`); the exact charge catalogue needs product confirmation before
   Stage 5 (billing).
