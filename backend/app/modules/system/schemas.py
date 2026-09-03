"""Response schemas for system/operational endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    version: str


class ReadinessDependency(BaseModel):
    name: str
    ok: bool


class ReadinessResponse(BaseModel):
    ready: bool
    dependencies: list[ReadinessDependency]
