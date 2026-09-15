"""Object storage abstraction.

File bytes live in object storage; only metadata lives in Postgres
(docs/DEVELOPMENT-RULES). ``LocalDiskStorage`` is the dev/default backend; an S3
backend can be added later behind the same ``Storage`` protocol without touching
callers. Storage keys are generated server-side — original filenames are never
trusted as paths.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...


def generate_key(prefix: str, extension: str) -> str:
    ext = extension.lstrip(".")
    return f"{prefix}/{uuid.uuid4().hex}.{ext}"


class LocalDiskStorage:
    """Stores files under a base directory. Keys are relative paths; traversal
    outside the base directory is refused."""

    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        target = (self._base / key).resolve()
        if self._base not in target.parents and target != self._base:
            raise ValueError("Invalid storage key")
        return target

    def put(self, key: str, data: bytes) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()


def get_storage() -> Storage:
    settings = get_settings()
    # Only the local backend is implemented in Phase 1; S3 is a future swap.
    return LocalDiskStorage(settings.document_storage_dir)
