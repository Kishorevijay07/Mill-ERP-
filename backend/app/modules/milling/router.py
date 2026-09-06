"""Milling HTTP endpoints: batches, start (consume), production, complete."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.milling import service
from app.modules.milling.schemas import (
    MillingBatchCreate,
    MillingBatchDetail,
    MillingBatchOut,
    ProductionCreate,
    RiceProductionOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["milling"])


@router.post(
    "/milling-batches",
    response_model=MillingBatchDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    payload: MillingBatchCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.MILLING_BATCH_CREATE)),
) -> MillingBatchDetail:
    batch = service.create_batch(db, payload, _actor(request, user))
    return MillingBatchDetail.model_validate(batch)


@router.get("/milling-batches", response_model=Page[MillingBatchOut])
def list_batches(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.MILLING_BATCH_VIEW)),
) -> Page[MillingBatchOut]:
    rows, total = service.list_batches(db, pagination.page, pagination.page_size)
    return Page[MillingBatchOut](
        items=[MillingBatchOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/milling-batches/{batch_id}", response_model=MillingBatchDetail)
def get_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.MILLING_BATCH_VIEW)),
) -> MillingBatchDetail:
    return MillingBatchDetail.model_validate(service.get_batch(db, batch_id))


@router.post("/milling-batches/{batch_id}/start", response_model=MillingBatchDetail)
def start_batch(
    batch_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.MILLING_BATCH_CREATE)),
) -> MillingBatchDetail:
    batch = service.start_batch(db, batch_id, _actor(request, user))
    return MillingBatchDetail.model_validate(batch)


@router.post(
    "/milling-batches/{batch_id}/productions",
    response_model=RiceProductionOut,
    status_code=status.HTTP_201_CREATED,
)
def record_production(
    batch_id: uuid.UUID,
    payload: ProductionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.MILLING_BATCH_CREATE)),
) -> RiceProductionOut:
    production = service.record_production(db, batch_id, payload, _actor(request, user))
    return RiceProductionOut.model_validate(production)


@router.post("/milling-batches/{batch_id}/complete", response_model=MillingBatchDetail)
def complete_batch(
    batch_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.MILLING_BATCH_CREATE)),
) -> MillingBatchDetail:
    batch = service.complete_batch(db, batch_id, _actor(request, user))
    return MillingBatchDetail.model_validate(batch)
