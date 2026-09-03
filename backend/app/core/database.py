"""Database engine and session management (SQLAlchemy 2.x).

A single Engine is created per process. Request-scoped sessions are provided to
API handlers via the ``get_db`` FastAPI dependency. Service-layer code owns
transaction boundaries explicitly (see docs/DATABASE-SPEC.md).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()


def _engine_kwargs(url: str) -> dict[str, object]:
    """Backend-specific engine options.

    PostgreSQL (production) uses a short connect timeout so the readiness probe
    fails fast instead of blocking. SQLite (hermetic tests) needs a different
    connect arg and cannot share a pooled connection across threads.
    """
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "connect_args": {"connect_timeout": 3}}


engine = create_engine(
    _settings.sqlalchemy_database_uri,
    echo=False,
    future=True,
    **_engine_kwargs(_settings.sqlalchemy_database_uri),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session.

    The session is always closed. Commits are the responsibility of the service
    layer so that multi-record business operations remain atomic.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Lightweight connectivity probe used by the readiness endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # readiness must never raise
        return False
