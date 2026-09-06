"""Settings HTTP endpoints: mill profile and charge rates."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.settings import service
from app.modules.settings.schemas import (
    ChargeRateCreate,
    ChargeRateOut,
    ChargeRateUpdate,
    MillSettingsOut,
    MillSettingsUpdate,
)

router = APIRouter(tags=["settings"])


@router.get("/mill-settings", response_model=MillSettingsOut)
def get_mill_settings(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.SETTINGS_VIEW)),
) -> MillSettingsOut:
    return MillSettingsOut.model_validate(service.get_or_create_mill_settings(db))


@router.put("/mill-settings", response_model=MillSettingsOut)
def update_mill_settings(
    payload: MillSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
) -> MillSettingsOut:
    settings = service.update_mill_settings(db, payload, _actor(request, user))
    return MillSettingsOut.model_validate(settings)


@router.get("/charge-rates", response_model=list[ChargeRateOut])
def list_charge_rates(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.SETTINGS_VIEW)),
) -> list[ChargeRateOut]:
    rows = service.list_charge_rates(db, active_only=active_only)
    return [ChargeRateOut.model_validate(r) for r in rows]


@router.post("/charge-rates", response_model=ChargeRateOut, status_code=status.HTTP_201_CREATED)
def create_charge_rate(
    payload: ChargeRateCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
) -> ChargeRateOut:
    rate = service.create_charge_rate(db, payload, _actor(request, user))
    return ChargeRateOut.model_validate(rate)


@router.put("/charge-rates/{rate_id}", response_model=ChargeRateOut)
def update_charge_rate(
    rate_id: uuid.UUID,
    payload: ChargeRateUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
) -> ChargeRateOut:
    rate = service.update_charge_rate(db, rate_id, payload, _actor(request, user))
    return ChargeRateOut.model_validate(rate)


@router.delete("/charge-rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_charge_rate(
    rate_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.SETTINGS_MANAGE)),
) -> Response:
    service.delete_charge_rate(db, rate_id, _actor(request, user))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
