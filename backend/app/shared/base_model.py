"""Declarative base and common mixins shared by all ORM models.

Establishes the conventions from docs/DATABASE-SPEC.md:
- UUID primary keys (server-generated) for core entities
- created_at / updated_at timestamps
- optional created_by / updated_by audit columns

The UUID column type is SQLAlchemy's dialect-agnostic ``Uuid``: it renders as a
native ``UUID`` on PostgreSQL and as ``CHAR(32)`` on other backends (e.g. SQLite
for fast, hermetic tests). Production runs on PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, MetaData, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint naming keeps Alembic autogenerate diffs reviewable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditActorMixin:
    """created_by / updated_by user references.

    Left nullable at the column level; individual modules add the foreign key to
    ``users`` once the auth module exists (Stage 1).
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
