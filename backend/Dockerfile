# syntax=docker/dockerfile:1

# ---- Base with uv ----
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1
# uv is copied from its official distroless image (pinned).
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/
WORKDIR /app

# ---- Dependencies layer (cached on lockfile) ----
FROM base AS deps
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev || \
    uv sync --no-install-project --no-dev

# ---- Runtime ----
FROM base AS runtime
# Non-root runtime user.
RUN useradd --create-home --uid 10001 appuser
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY . .
USER appuser
EXPOSE 8000
# Liveness probe target: /health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
