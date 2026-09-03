"""Authentication and RBAC authorization tests.

Covers password hashing, the login/session/logout lifecycle, and per-role
permission enforcement through a guarded endpoint mounted for testing.
"""

from __future__ import annotations

from fastapi import Depends

from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.main import app
from app.modules.auth import service
from app.modules.auth.dependencies import require_permission
from app.modules.auth.permissions import Permission

# A test-only endpoint guarded by a specific permission, used to assert that RBAC
# is enforced server-side regardless of role.
_GUARD_PATH = "/api/v1/_test/needs-load-accept"


@app.get(_GUARD_PATH)
def _needs_load_accept(
    _user=Depends(require_permission(Permission.GOVERNMENT_LOAD_ACCEPT)),
) -> dict[str, bool]:
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _login(client, identifier: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )


# --------------------------------------------------------------------------- #
# Password hashing (unit)
# --------------------------------------------------------------------------- #
def test_password_hash_is_not_plaintext_and_verifies() -> None:
    hashed = hash_password("s3cret-password")
    assert hashed != "s3cret-password"
    assert hashed.startswith("$argon2")
    assert verify_password("s3cret-password", hashed) is True
    assert verify_password("wrong", hashed) is False


# --------------------------------------------------------------------------- #
# Effective permissions per role (unit)
# --------------------------------------------------------------------------- #
def test_effective_permissions_per_role(make_user) -> None:
    make_user(email="staff@example.com", username="staff", role_codes=("STAFF",))
    make_user(email="owner@example.com", username="owner", role_codes=("OWNER",))
    make_user(
        email="admin@example.com",
        username="admin",
        role_codes=("ADMIN",),
        is_superuser=True,
    )

    with SessionLocal() as db:
        staff = service.get_user_by_identifier(db, "staff")
        owner = service.get_user_by_identifier(db, "owner")
        admin = service.get_user_by_identifier(db, "admin")
        assert staff and owner and admin

        staff_perms = service.effective_permissions(staff)
        owner_perms = service.effective_permissions(owner)
        admin_perms = service.effective_permissions(admin)

    # Staff can view but not accept loads.
    assert Permission.GOVERNMENT_LOAD_VIEW in staff_perms
    assert Permission.GOVERNMENT_LOAD_ACCEPT not in staff_perms
    # Owner can accept loads and record payments.
    assert Permission.GOVERNMENT_LOAD_ACCEPT in owner_perms
    assert Permission.PAYMENT_RECORD in owner_perms
    # Owner is not an administrator.
    assert Permission.SETTINGS_MANAGE not in owner_perms
    # Admin/superuser holds everything.
    assert Permission.SETTINGS_MANAGE in admin_perms
    assert Permission.USERS_MANAGE in admin_perms


# --------------------------------------------------------------------------- #
# Login / session / logout lifecycle
# --------------------------------------------------------------------------- #
def test_login_success_sets_cookie_and_returns_permissions(client, make_user) -> None:
    make_user(
        email="owner@example.com",
        username="owner",
        password="hunter2-hunter2",
        role_codes=("OWNER",),
    )
    resp = _login(client, "owner@example.com", "hunter2-hunter2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "owner"
    assert "OWNER" in body["roles"]
    assert Permission.GOVERNMENT_LOAD_ACCEPT in body["permissions"]
    # Session cookie issued, HttpOnly.
    from app.core.config import get_settings

    cookie_name = get_settings().session_cookie_name
    assert cookie_name in resp.cookies
    set_cookie = resp.headers.get("set-cookie", "")
    assert "httponly" in set_cookie.lower()


def test_login_can_use_username(client, make_user) -> None:
    make_user(
        email="staff@example.com",
        username="staff1",
        password="passphrase-123",
        role_codes=("STAFF",),
    )
    resp = _login(client, "staff1", "passphrase-123")
    assert resp.status_code == 200


def test_login_wrong_password_is_401(client, make_user) -> None:
    make_user(email="u@example.com", username="u", password="right-password")
    resp = _login(client, "u@example.com", "wrong-password")
    assert resp.status_code == 401
    assert resp.json()["error"]["message"] == "Invalid credentials"


def test_login_unknown_user_is_401(client) -> None:
    resp = _login(client, "ghost@example.com", "whatever")
    assert resp.status_code == 401


def test_inactive_user_cannot_login(client, make_user) -> None:
    make_user(
        email="gone@example.com",
        username="gone",
        password="still-secret-99",
        is_active=False,
    )
    resp = _login(client, "gone@example.com", "still-secret-99")
    assert resp.status_code == 401


def test_me_requires_authentication(client) -> None:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_after_login(client, make_user) -> None:
    make_user(
        email="owner@example.com",
        username="owner",
        password="hunter2-hunter2",
        role_codes=("OWNER",),
    )
    _login(client, "owner@example.com", "hunter2-hunter2")
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "owner@example.com"


def test_logout_revokes_session(client, make_user) -> None:
    make_user(
        email="owner@example.com",
        username="owner",
        password="hunter2-hunter2",
        role_codes=("OWNER",),
    )
    _login(client, "owner@example.com", "hunter2-hunter2")
    assert client.get("/api/v1/auth/me").status_code == 200

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    # Even if a stale cookie were replayed, the session is revoked server-side.
    assert client.get("/api/v1/auth/me").status_code == 401


# --------------------------------------------------------------------------- #
# RBAC enforcement through a guarded endpoint
# --------------------------------------------------------------------------- #
def test_guarded_endpoint_rejects_unauthenticated(client) -> None:
    assert client.get(_GUARD_PATH).status_code == 401


def test_guarded_endpoint_allows_permitted_role(client, make_user) -> None:
    make_user(
        email="owner@example.com",
        username="owner",
        password="hunter2-hunter2",
        role_codes=("OWNER",),
    )
    _login(client, "owner@example.com", "hunter2-hunter2")
    assert client.get(_GUARD_PATH).status_code == 200


def test_guarded_endpoint_forbids_role_without_permission(client, make_user) -> None:
    make_user(
        email="staff@example.com",
        username="staff",
        password="passphrase-123",
        role_codes=("STAFF",),
    )
    _login(client, "staff@example.com", "passphrase-123")
    resp = client.get(_GUARD_PATH)
    assert resp.status_code == 403
    assert resp.json()["error"]["message"] == "Insufficient permissions"


def test_superuser_admin_passes_any_guard(client, make_user) -> None:
    make_user(
        email="admin@example.com",
        username="admin",
        password="admin-passphrase-1",
        role_codes=("ADMIN",),
        is_superuser=True,
    )
    _login(client, "admin@example.com", "admin-passphrase-1")
    assert client.get(_GUARD_PATH).status_code == 200
