"""Cross-cutting request/actor context passed into service functions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ActorContext:
    """Who is performing an action, for created_by/updated_by stamping and audit."""

    user_id: uuid.UUID
    request_id: str | None = None
    ip_address: str | None = None
