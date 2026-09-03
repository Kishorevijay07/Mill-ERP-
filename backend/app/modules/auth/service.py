"""Authentication & session domain logic.

Kept free of FastAPI/HTTP concerns so it is unit-testable and reusable. HTTP
wiring (cookies, status codes) lives in the router; request-scoped access lives
in dependencies.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.modules.auth.models import User, UserSession
from app.modules.auth.permissions import ALL_PERMISSIONS, RoleCode

# A valid Argon2 hash of a throwaway value, used only to equalize timing on the
# unknown-user authentication path so account existence does not leak.
_DUMMY_HASH = hash_password("timing-equalization-placeholder")


def _now() -> datetime:
    return datetime.now(UTC)


def _as_aware_utc(value: datetime) -> datetime:
    """Coerce a possibly-naive DB timestamp to aware UTC.

    PostgreSQL returns timezone-aware datetimes; SQLite (tests) returns naive
    ones. Normalizing here keeps comparisons correct on both backends.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    """Look up a user by email or username (case-insensitive on email)."""
    normalized = identifier.strip()
    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where((User.email == normalized.lower()) | (User.username == normalized))
    )
    return db.execute(stmt).scalar_one_or_none()


def authenticate(db: Session, identifier: str, password: str) -> User | None:
    """Return the user when credentials are valid and the account is active.

    Always runs a password verification (even for unknown users) to avoid
    leaking account existence through response timing.
    """
    user = get_user_by_identifier(db, identifier)
    if user is None:
        # Dummy verify to equalize timing against the unknown-user path.
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def effective_permissions(user: User) -> set[str]:
    """Union of permission codes granted by the user's roles.

    Superusers and members of the ADMIN role receive the full catalogue.
    """
    if user.is_superuser or any(role.code == RoleCode.ADMIN for role in user.roles):
        return set(ALL_PERMISSIONS)
    granted: set[str] = set()
    for role in user.roles:
        granted.update(perm.code for perm in role.permissions)
    return granted


def create_session(
    db: Session,
    user: User,
    *,
    ttl_seconds: int,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> str:
    """Create a persisted session and return the raw (unhashed) token.

    Only the token hash is stored; the raw token is placed in the cookie.
    """
    raw_token = generate_session_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        expires_at=_now() + timedelta(seconds=ttl_seconds),
        user_agent=user_agent[:512] if user_agent else None,
        ip_address=ip_address[:64] if ip_address else None,
    )
    db.add(session)
    db.commit()
    return raw_token


def resolve_session(db: Session, raw_token: str) -> User | None:
    """Return the active user for a valid, unexpired, unrevoked session token."""
    token_hash = hash_session_token(raw_token)
    stmt = (
        select(UserSession)
        .options(
            selectinload(UserSession.user).selectinload(User.roles),
        )
        .where(UserSession.token_hash == token_hash)
    )
    session = db.execute(stmt).scalar_one_or_none()
    if session is None or session.revoked_at is not None:
        return None
    if _as_aware_utc(session.expires_at) <= _now():
        return None
    user = session.user
    if not user.is_active:
        return None
    return user


def revoke_session(db: Session, raw_token: str) -> None:
    """Revoke the session for a raw token, if one exists (idempotent)."""
    token_hash = hash_session_token(raw_token)
    stmt = select(UserSession).where(UserSession.token_hash == token_hash)
    session = db.execute(stmt).scalar_one_or_none()
    if session is not None and session.revoked_at is None:
        session.revoked_at = _now()
        db.commit()


def get_user_roles(user: User) -> list[str]:
    return sorted(role.code for role in user.roles)
