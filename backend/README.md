# Rice Mill ERP — Backend

FastAPI modular monolith. See the repository root `README.md` for the full stack and
the `docs/` folder for the product and domain specifications.

## Quick start (local, without Docker)

```bash
cd backend
uv sync --extra dev            # create .venv and install deps
cp ../.env.example ../.env     # then edit values
uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the OpenAPI UI, and http://localhost:8000/health.

## Common commands

```bash
uv run pytest                  # tests
uv run ruff check .            # lint
uv run ruff format .           # format
uv run mypy                    # type check
uv run alembic upgrade head    # apply migrations (needs a running Postgres)
uv run alembic revision --autogenerate -m "message"
```

## Layout

```
app/
  main.py              # app factory, middleware, router wiring, lifespan
  core/                # config, logging, database engine/session
  api/v1/              # versioned API router aggregation
  modules/             # feature/domain modules (thin routers -> services)
    system/            # health & readiness (Phase 0)
  shared/              # cross-cutting base model + mixins
migrations/            # Alembic environment + versions
tests/                 # pytest
```

Business modules (government, receiving, milling, rice, delivery, billing, inventory)
are added from Stage 1 onward — Phase 0 only establishes the foundation.
