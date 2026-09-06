"""Rice HTTP endpoints: QC decisions and rice stock."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.rice import service
from app.modules.rice.schemas import (
    QCPassResponse,
    QualityDecision,
    RiceLotOut,
    RiceLotWithStock,
    RiceQualityOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["rice"])


@router.get("/rice-quality", response_model=Page[RiceQualityOut])
def list_quality(
    pagination: Pagination = Depends(),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.RICE_STOCK_VIEW)),
) -> Page[RiceQualityOut]:
    rows, total = service.list_quality(db, status, pagination.page, pagination.page_size)
    return Page[RiceQualityOut](
        items=[RiceQualityOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/rice-quality/{quality_id}", response_model=RiceQualityOut)
def get_quality(
    quality_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.RICE_STOCK_VIEW)),
) -> RiceQualityOut:
    return RiceQualityOut.model_validate(service.get_quality(db, quality_id))


@router.post("/rice-quality/{quality_id}/pass", response_model=QCPassResponse)
def pass_quality(
    quality_id: uuid.UUID,
    request: Request,
    payload: QualityDecision | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.RICE_QC_APPROVE)),
) -> QCPassResponse:
    quality, lot = service.pass_quality(
        db, quality_id, payload or QualityDecision(), _actor(request, user)
    )
    return QCPassResponse(
        quality=RiceQualityOut.model_validate(quality),
        rice_lot=RiceLotOut.model_validate(lot),
    )


@router.post("/rice-quality/{quality_id}/fail", response_model=RiceQualityOut)
def fail_quality(
    quality_id: uuid.UUID,
    request: Request,
    payload: QualityDecision | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.RICE_QC_APPROVE)),
) -> RiceQualityOut:
    quality = service.fail_quality(
        db, quality_id, payload or QualityDecision(), _actor(request, user)
    )
    return RiceQualityOut.model_validate(quality)


@router.get("/rice-lots", response_model=Page[RiceLotWithStock])
def list_rice_lots(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.RICE_STOCK_VIEW)),
) -> Page[RiceLotWithStock]:
    rows = service.list_rice_lots(db)
    items = [
        RiceLotWithStock(**RiceLotOut.model_validate(lot).model_dump(), available_kg=available)
        for lot, available in rows
    ]
    total = len(items)
    start = (pagination.page - 1) * pagination.page_size
    return Page[RiceLotWithStock](
        items=items[start : start + pagination.page_size],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/rice-lots/{lot_id}", response_model=RiceLotWithStock)
def get_rice_lot(
    lot_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.RICE_STOCK_VIEW)),
) -> RiceLotWithStock:
    lot, available = service.get_rice_lot(db, lot_id)
    return RiceLotWithStock(**RiceLotOut.model_validate(lot).model_dump(), available_kg=available)
