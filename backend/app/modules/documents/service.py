"""Document storage service: store bytes + persist metadata, and read back."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.documents.models import Document
from app.modules.documents.storage import generate_key, get_storage
from app.shared.errors import NotFoundError


def store_document(
    db: Session,
    *,
    entity_type: str,
    entity_id: uuid.UUID | None,
    filename: str,
    content_type: str,
    data: bytes,
    key_prefix: str,
    extension: str,
    created_by: uuid.UUID | None = None,
) -> Document:
    """Write bytes to storage and persist metadata (no commit — caller owns it)."""
    key = generate_key(key_prefix, extension)
    get_storage().put(key, data)
    document = Document(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(data),
        storage_key=key,
        created_by=created_by,
    )
    db.add(document)
    db.flush()
    return document


def get_document(db: Session, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found")
    return document


def read_document_bytes(document: Document) -> bytes:
    return get_storage().get(document.storage_key)
