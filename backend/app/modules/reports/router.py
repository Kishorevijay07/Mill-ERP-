"""Reporting endpoints: dashboard KPIs."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.billing.models import ClaimStatus, GovernmentClaim, Payment
from app.modules.delivery.models import Dispatch, DispatchStatus
from app.modules.inventory.models import (
    InventoryItemType,
    InventoryTransaction,
    InventoryTransactionType,
)

router = APIRouter(tags=["reports"])


class DashboardKpis(BaseModel):
    paddy_received_kg: Decimal
    paddy_available_kg: Decimal
    rice_stock_kg: Decimal
    pending_delivery: int
    claims_pending: int
    amount_paid: Decimal
    amount_outstanding: Decimal


def _sum_qty(db: Session, *, item_type: str, txn_type: str | None = None) -> Decimal:
    stmt = select(func.coalesce(func.sum(InventoryTransaction.quantity_kg), 0)).where(
        InventoryTransaction.item_type == item_type
    )
    if txn_type is not None:
        stmt = stmt.where(InventoryTransaction.transaction_type == txn_type)
    return Decimal(db.execute(stmt).scalar_one())


@router.get("/reports/dashboard", response_model=DashboardKpis)
def dashboard(
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.REPORTS_VIEW)),
) -> DashboardKpis:
    paddy_received = _sum_qty(
        db,
        item_type=InventoryItemType.PADDY_LOT,
        txn_type=InventoryTransactionType.PADDY_RECEIPT,
    )
    paddy_available = _sum_qty(db, item_type=InventoryItemType.PADDY_LOT)
    rice_stock = _sum_qty(db, item_type=InventoryItemType.RICE_LOT)

    pending_delivery = db.execute(
        select(func.count())
        .select_from(Dispatch)
        .where(Dispatch.status == DispatchStatus.DISPATCHED)
    ).scalar_one()

    claims_pending = db.execute(
        select(func.count())
        .select_from(GovernmentClaim)
        .where(
            GovernmentClaim.status.in_(
                [ClaimStatus.SUBMITTED, ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_PAID]
            )
        )
    ).scalar_one()

    amount_paid = Decimal(
        db.execute(select(func.coalesce(func.sum(Payment.amount), 0))).scalar_one()
    )
    net_non_draft = Decimal(
        db.execute(
            select(func.coalesce(func.sum(GovernmentClaim.net_amount), 0)).where(
                GovernmentClaim.status != ClaimStatus.DRAFT
            )
        ).scalar_one()
    )
    amount_outstanding = net_non_draft - amount_paid
    if amount_outstanding < 0:
        amount_outstanding = Decimal("0")

    return DashboardKpis(
        paddy_received_kg=paddy_received,
        paddy_available_kg=paddy_available,
        rice_stock_kg=rice_stock,
        pending_delivery=pending_delivery,
        claims_pending=claims_pending,
        amount_paid=amount_paid,
        amount_outstanding=amount_outstanding,
    )
