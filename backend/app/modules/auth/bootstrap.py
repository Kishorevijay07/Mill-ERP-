"""Idempotent seeding for RBAC: system roles and user creation.

Used by the management CLI (``app.cli``) to provision the initial admin and by
tests to build fixtures. Seeding roles here (rather than in a data migration)
keeps the permission catalogue as the single source of truth in code.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.modules.auth.models import Role, RolePermission, User
from app.modules.auth.permissions import (
    DEFAULT_ROLE_DESCRIPTIONS,
    DEFAULT_ROLE_PERMISSIONS,
    RoleCode,
)


def seed_system_roles(db: Session) -> None:
    """Create/refresh the ADMIN/OWNER/STAFF roles and their permission grants.

    Idempotent: safe to run repeatedly. Permission grants are synced to the
    catalogue so code remains authoritative.
    """
    for role_code, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        role = db.execute(
            select(Role).options(selectinload(Role.permissions)).where(Role.code == role_code)
        ).scalar_one_or_none()

        if role is None:
            role = Role(
                code=role_code,
                name=role_code.capitalize(),
                description=DEFAULT_ROLE_DESCRIPTIONS.get(role_code),
                is_system=True,
            )
            db.add(role)
            db.flush()

        existing = {perm.code for perm in role.permissions}
        desired = set(permissions)
        for code in desired - existing:
            db.add(RolePermission(role_id=role.id, code=code))
        for perm in list(role.permissions):
            if perm.code not in desired:
                db.delete(perm)

    db.commit()


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    full_name: str,
    password: str,
    role_codes: Iterable[str] = (),
    is_superuser: bool = False,
    is_active: bool = True,
) -> User:
    """Create a user, hashing the password and attaching the given roles."""
    user = User(
        email=email.strip().lower(),
        username=username.strip(),
        full_name=full_name.strip(),
        hashed_password=hash_password(password),
        is_superuser=is_superuser,
        is_active=is_active,
    )
    role_code_list = list(role_codes)
    if role_code_list:
        roles = db.execute(select(Role).where(Role.code.in_(role_code_list))).scalars().all()
        found = {role.code for role in roles}
        missing = set(role_code_list) - found
        if missing:
            raise ValueError(f"Unknown role codes: {sorted(missing)}")
        user.roles = list(roles)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def role_code_choices() -> list[str]:
    return [rc.value for rc in RoleCode]
