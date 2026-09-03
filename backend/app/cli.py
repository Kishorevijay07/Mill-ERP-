"""Management CLI for operational bootstrap tasks.

Usage (from the backend directory, with a running/migrated database):

    uv run python -m app.cli seed-roles
    uv run python -m app.cli create-admin --email admin@example.com \
        --username admin --full-name "Site Admin"

The admin password is read from the ADMIN_PASSWORD environment variable, or
prompted interactively — never passed on the command line.
"""

from __future__ import annotations

import argparse
import os
import sys
from getpass import getpass

from app.core.database import SessionLocal
from app.modules.auth import bootstrap
from app.modules.auth.permissions import RoleCode


def _read_password(env_var: str) -> str:
    password = os.environ.get(env_var)
    if password:
        return password
    password = getpass("Password: ")
    confirm = getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(2)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        raise SystemExit(2)
    return password


def _cmd_seed_roles(_: argparse.Namespace) -> None:
    with SessionLocal() as db:
        bootstrap.seed_system_roles(db)
    print("System roles seeded (ADMIN, OWNER, STAFF).")


def _cmd_create_admin(args: argparse.Namespace) -> None:
    password = _read_password("ADMIN_PASSWORD")
    with SessionLocal() as db:
        bootstrap.seed_system_roles(db)
        user = bootstrap.create_user(
            db,
            email=args.email,
            username=args.username,
            full_name=args.full_name,
            password=password,
            role_codes=[RoleCode.ADMIN],
            is_superuser=True,
        )
    print(f"Created admin user {user.username} <{user.email}> ({user.id}).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed-roles", help="Create/refresh system roles").set_defaults(
        func=_cmd_seed_roles
    )

    admin = sub.add_parser("create-admin", help="Create a superuser admin account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--username", required=True)
    admin.add_argument("--full-name", required=True)
    admin.set_defaults(func=_cmd_create_admin)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
