"""Shared pytest fixtures.

Tests run against a hermetic file-backed SQLite database (no external services).
The database URL and a valid SECRET_KEY are set before the app/settings are
imported so configuration validation passes deterministically.

The schema is (re)created and system roles seeded before each test, giving every
test a clean, isolated database.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Configure the environment before importing anything that reads settings.
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-16-chars")
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_rmerp.db")

# Invoice-only build: the government/receiving/milling/rice/delivery/billing HTTP
# routers are unregistered (see app/api/v1/router.py), so their endpoint tests
# cannot run. Skip collecting them here. Re-register the routers and remove the
# matching entries below to bring those suites back.
collect_ignore = [
    "test_billing.py",
    "test_delivery.py",
    "test_government.py",
    "test_milling.py",
    "test_receiving.py",
]


@pytest.fixture(autouse=True)
def _database() -> Iterator[None]:
    """Fresh schema + seeded system roles per test."""
    import app.shared.models  # noqa: F401  (register all ORM models)
    from app.core.database import SessionLocal, engine
    from app.modules.auth.bootstrap import seed_system_roles
    from app.shared.base_model import Base

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_system_roles(db)

    yield

    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session() -> Iterator[object]:
    from app.core.database import SessionLocal

    with SessionLocal() as session:
        yield session


@pytest.fixture()
def client() -> Iterator[object]:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def make_user():
    """Factory to create a user with roles in the test database."""
    from app.core.database import SessionLocal
    from app.modules.auth import bootstrap

    def _make(
        *,
        email: str,
        username: str,
        password: str = "correct horse battery staple",
        full_name: str = "Test User",
        role_codes: tuple[str, ...] = (),
        is_superuser: bool = False,
        is_active: bool = True,
    ):
        with SessionLocal() as db:
            return bootstrap.create_user(
                db,
                email=email,
                username=username,
                full_name=full_name,
                password=password,
                role_codes=role_codes,
                is_superuser=is_superuser,
                is_active=is_active,
            )

    return _make
