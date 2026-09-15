"""Receiving HTTP endpoints: weighment, paddy QC, accept/reject, and paddy stock.

State transitions are explicit action endpoints on the load. Authorization is
enforced server-side per action.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.government.schemas import LoadOut
from app.modules.receiving import service
from app.modules.receiving.schemas import (
    AcceptResponse,
    PaddyLotOut,
    PaddyLotWithStock,
    PaddyQualityCreate,
    PaddyQualityOut,
    RejectRequest,
    WeighmentCreate,
    WeighmentOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["receiving"])


# --------------------------------------------------------------------------- #
# Weighment
# --------------------------------------------------------------------------- #
@router.post(
    "/government-loads/{load_id}/weighments",
    response_model=WeighmentOut,
    status_code=status.HTTP_201_CREATED,
)
def record_weighment(
    load_id: uuid.UUID,
    payload: WeighmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.RECEIVING_WEIGHMENT_RECORD)),
) -> WeighmentOut:
    weighment = service.record_weighment(db, load_id, payload, _actor(request, user))
    return WeighmentOut.model_validate(weighment)


@router.get(
    "/government-loads/{load_id}/weighments",
    response_model=list[WeighmentOut],
)
def list_weighments(
    load_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_VIEW)),
) -> list[WeighmentOut]:
    rows = service.list_weighments(db, load_id)
    return [WeighmentOut.model_validate(r) for r in rows]


# --------------------------------------------------------------------------- #
# Paddy quality
# --------------------------------------------------------------------------- #
@router.post(
    "/government-loads/{load_id}/paddy-quality",
    response_model=PaddyQualityOut,
    status_code=status.HTTP_201_CREATED,
)
def record_paddy_quality(
    load_id: uuid.UUID,
    payload: PaddyQualityCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.RECEIVING_PADDY_QC_RECORD)),
) -> PaddyQualityOut:
    quality = service.record_paddy_quality(db, load_id, payload, _actor(request, user))
    return PaddyQualityOut.model_validate(quality)


@router.get(
    "/government-loads/{load_id}/paddy-quality",
    response_model=PaddyQualityOut,
)
def get_paddy_quality(
    load_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_VIEW)),
) -> PaddyQualityOut:
    return PaddyQualityOut.model_validate(service.get_paddy_quality(db, load_id))


# --------------------------------------------------------------------------- #
# Accept / reject
# --------------------------------------------------------------------------- #
@router.post("/government-loads/{load_id}/accept", response_model=AcceptResponse)
def accept_load(
    load_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_ACCEPT)),
) -> AcceptResponse:
    load, paddy_lot = service.accept_load(db, load_id, _actor(request, user))
    return AcceptResponse(
        load=LoadOut.model_validate(load),
        paddy_lot=PaddyLotOut.model_validate(paddy_lot),
    )


@router.post("/government-loads/{load_id}/reject", response_model=LoadOut)
def reject_load(
    load_id: uuid.UUID,
    request: Request,
    payload: RejectRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_ACCEPT)),
) -> LoadOut:
    reason = payload.reason if payload else None
    load = service.reject_load(db, load_id, reason, _actor(request, user))
    return LoadOut.model_validate(load)


# --------------------------------------------------------------------------- #
# Paddy lots / stock
# --------------------------------------------------------------------------- #
@router.get("/paddy-lots", response_model=Page[PaddyLotWithStock])
def list_paddy_lots(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.PADDY_STOCK_VIEW)),
) -> Page[PaddyLotWithStock]:
    rows = service.list_paddy_lots(db)
    items = [
        PaddyLotWithStock(
            **PaddyLotOut.model_validate(lot).model_dump(),
            available_kg=available,
        )
        for lot, available in rows
    ]
    total = len(items)
    start = (pagination.page - 1) * pagination.page_size
    page_items = items[start : start + pagination.page_size]
    return Page[PaddyLotWithStock](
        items=page_items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/paddy-lots/{lot_id}", response_model=PaddyLotWithStock)
def get_paddy_lot(
    lot_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.PADDY_STOCK_VIEW)),
) -> PaddyLotWithStock:
    lot, available = service.get_paddy_lot(db, lot_id)
    return PaddyLotWithStock(
        **PaddyLotOut.model_validate(lot).model_dump(),
        available_kg=available,
    )
