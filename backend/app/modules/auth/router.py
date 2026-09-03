"""Auth HTTP endpoints: login, logout, and current-user (/me).

Sessions are carried in an HttpOnly cookie. Cookie flags come from settings so
Secure can be enforced in staging/production. SameSite=Lax mitigates CSRF for
cross-site POSTs while keeping normal top-level navigation working.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    MessageResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("app.auth")


def _set_session_cookie(response: Response, raw_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )


@router.post("/login", response_model=MeResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MeResponse:
    settings = get_settings()
    user = service.authenticate(db, payload.identifier, payload.password)
    if user is None:
        # Uniform error — never reveal whether the account exists.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    raw_token = service.create_session(
        db,
        user,
        ttl_seconds=settings.session_ttl_seconds,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_session_cookie(response, raw_token)
    log.info("login_success", user_id=str(user.id))

    return MeResponse(
        user=UserOut.model_validate(user),
        roles=service.get_user_roles(user),
        permissions=sorted(service.effective_permissions(user)),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> MessageResponse:
    settings = get_settings()
    raw_token = request.cookies.get(settings.session_cookie_name)
    if raw_token:
        service.revoke_session(db, raw_token)
    _clear_session_cookie(response)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        user=UserOut.model_validate(current_user),
        roles=service.get_user_roles(current_user),
        permissions=sorted(service.effective_permissions(current_user)),
    )
