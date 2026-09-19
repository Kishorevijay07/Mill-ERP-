"""Document metadata.

Bytes live either in the database (``content``, the default — persists on hosts
with an ephemeral filesystem such as Render's free tier) or on object/disk
storage keyed by ``storage_key`` (see storage.py). Exactly one is populated per
document, decided by ``DOCUMENT_STORAGE_BACKEND``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, LargeBinary, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "documents"

    # Polymorphic owner reference (validated server-side by the creating module).
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Key into object/disk storage (local backend); a sentinel when bytes are
    # stored in the DB instead.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    # Raw bytes when stored in the database backend; NULL for disk-backed docs.
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
