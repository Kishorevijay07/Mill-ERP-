"""Operational endpoints: liveness (/health) and readiness (/ready).

- ``/health`` is a cheap liveness probe: the process is up. It must not touch
  external dependencies so it stays fast and always-answering.
- ``/ready`` verifies critical dependencies (database) and returns 503 when the
  service cannot serve traffic. Used by orchestrators and load balancers.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app import __version__
from app.core.config import get_settings
from app.core.database import check_database_connection
from app.modules.system.schemas import (
    HealthResponse,
    ReadinessDependency,
    ReadinessResponse,
)

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        version=__version__,
    )


@router.get("/ready", response_model=ReadinessResponse)
def ready(response: Response) -> ReadinessResponse:
    db_ok = check_database_connection()
    dependencies = [ReadinessDependency(name="database", ok=db_ok)]
    all_ok = all(dep.ok for dep in dependencies)
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(ready=all_ok, dependencies=dependencies)
