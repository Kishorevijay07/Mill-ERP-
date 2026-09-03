"""FastAPI dependencies for authentication and RBAC authorization.

- ``get_current_user`` resolves the session cookie to an active user (401 if not).
- ``require_permission(code)`` builds a dependency that enforces a permission
  server-side (403 if missing). Authorization is always enforced here, never by
  the frontend.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.modules.auth import service
from app.modules.auth.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user = service.resolve_session(db, raw_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return user


def require_permission(code: str) -> Callable[[User], User]:
    """Return a dependency that allows the request only if the current user holds
    ``code`` (superusers/ADMIN implicitly hold every permission)."""

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if code not in service.effective_permissions(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _dependency
