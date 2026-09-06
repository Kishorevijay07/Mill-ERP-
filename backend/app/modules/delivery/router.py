"""Dispatch & delivery HTTP endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.delivery import service
from app.modules.delivery.schemas import (
    DeliveryReceiptCreate,
    DeliveryReceiptOut,
    DispatchCreate,
    DispatchDetail,
    DispatchOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["delivery"])


# --------------------------------------------------------------------------- #
# Dispatches
# --------------------------------------------------------------------------- #
@router.post("/dispatches", response_model=DispatchDetail, status_code=status.HTTP_201_CREATED)
def create_dispatch(
    payload: DispatchCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.DISPATCH_CREATE)),
) -> DispatchDetail:
    dispatch = service.create_dispatch(db, payload, _actor(request, user))
    return DispatchDetail.model_validate(dispatch)


@router.get("/dispatches", response_model=Page[DispatchOut])
def list_dispatches(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.DISPATCH_VIEW)),
) -> Page[DispatchOut]:
    rows, total = service.list_dispatches(db, pagination.page, pagination.page_size)
    return Page[DispatchOut](
        items=[DispatchOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/dispatches/{dispatch_id}", response_model=DispatchDetail)
def get_dispatch(
    dispatch_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.DISPATCH_VIEW)),
) -> DispatchDetail:
    return DispatchDetail.model_validate(service.get_dispatch(db, dispatch_id))


@router.post("/dispatches/{dispatch_id}/prepare", response_model=DispatchDetail)
def prepare_dispatch(
    dispatch_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.DISPATCH_CREATE)),
) -> DispatchDetail:
    dispatch = service.prepare_dispatch(db, dispatch_id, _actor(request, user))
    return DispatchDetail.model_validate(dispatch)


@router.post("/dispatches/{dispatch_id}/dispatch", response_model=DispatchDetail)
def dispatch_dispatch(
    dispatch_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.DISPATCH_CONFIRM)),
) -> DispatchDetail:
    dispatch = service.dispatch_dispatch(db, dispatch_id, _actor(request, user))
    return DispatchDetail.model_validate(dispatch)


@router.post(
    "/dispatches/{dispatch_id}/delivery-receipt",
    response_model=DeliveryReceiptOut,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery_receipt(
    dispatch_id: uuid.UUID,
    payload: DeliveryReceiptCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.DISPATCH_CONFIRM)),
) -> DeliveryReceiptOut:
    receipt = service.create_delivery_receipt(db, dispatch_id, payload, _actor(request, user))
    return DeliveryReceiptOut.model_validate(receipt)


# --------------------------------------------------------------------------- #
# Delivery receipts
# --------------------------------------------------------------------------- #
@router.get("/delivery-receipts", response_model=Page[DeliveryReceiptOut])
def list_receipts(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.DISPATCH_VIEW)),
) -> Page[DeliveryReceiptOut]:
    rows, total = service.list_receipts(db, pagination.page, pagination.page_size)
    return Page[DeliveryReceiptOut](
        items=[DeliveryReceiptOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/delivery-receipts/{receipt_id}", response_model=DeliveryReceiptOut)
def get_receipt(
    receipt_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.DISPATCH_VIEW)),
) -> DeliveryReceiptOut:
    return DeliveryReceiptOut.model_validate(service.get_receipt(db, receipt_id))
