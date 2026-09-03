"""Cross-cutting security primitives: password hashing and session tokens.

Password hashing uses Argon2id (via pwdlib) — no 72-byte truncation and modern
memory-hard parameters. Session tokens are high-entropy opaque strings; only a
SHA-256 hash of a token is stored, so a database disclosure never yields a live
session credential.
"""

from __future__ import annotations

import hashlib
import secrets

from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

# Number of URL-safe bytes of entropy in a raw session token.
_SESSION_TOKEN_BYTES = 32


def hash_password(plain_password: str) -> str:
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _password_hash.verify(plain_password, hashed_password)


def generate_session_token() -> str:
    """Return a new opaque, URL-safe session token (the raw secret)."""
    return secrets.token_urlsafe(_SESSION_TOKEN_BYTES)


def hash_session_token(raw_token: str) -> str:
    """Deterministic hash of a session token for at-rest storage/lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
