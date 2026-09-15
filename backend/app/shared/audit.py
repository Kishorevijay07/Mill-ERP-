"""Audit trail: an append-only record of important business mutations.

Every significant operation (create, state transition, stock movement, claim,
payment, config/permission change) records an ``AuditLog`` row capturing who did
what to which entity, with optional before/after snapshots. Completed business
records are never silently deleted — cancellation/reversal is modelled explicitly
by later modules; the audit log preserves history regardless.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.shared.base_model import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_logs"

    # Actor may be null for system-initiated actions.
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Optional business reference of the affected record (e.g. LD-000001).
    entity_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


def record_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | str | None = None,
    entity_reference: str | None = None,
    user_id: uuid.UUID | None = None,
    before_data: dict[str, Any] | None = None,
    after_data: dict[str, Any] | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Append an audit entry within the caller's transaction (no commit here)."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        entity_reference=entity_reference,
        before_data=before_data,
        after_data=after_data,
        request_id=request_id,
        ip_address=ip_address,
    )
    db.add(entry)
    return entry
