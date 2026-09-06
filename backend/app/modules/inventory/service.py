"""Inventory posting and balance queries.

``post_transaction`` appends a signed movement within the caller's transaction
(no commit). ``available_quantity`` returns the current balance for a lot.

Concurrency note: to prevent overspend, a caller posting a *consumption*
(negative) must hold a row lock on the owning lot for the duration of the
transaction (SELECT ... FOR UPDATE). This function additionally refuses a
movement that would drive the balance negative, as defence in depth.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory.models import (
    InventoryItemType,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.shared.errors import DomainError


class InsufficientStockError(DomainError):
    code = "insufficient_stock"
    status_code = 409


def available_quantity(
    db: Session, item_type: InventoryItemType | str, item_id: uuid.UUID
) -> Decimal:
    total = db.execute(
        select(func.coalesce(func.sum(InventoryTransaction.quantity_kg), 0)).where(
            InventoryTransaction.item_type == str(item_type),
            InventoryTransaction.item_id == item_id,
        )
    ).scalar_one()
    return Decimal(total)


def post_transaction(
    db: Session,
    *,
    item_type: InventoryItemType,
    item_id: uuid.UUID,
    quantity_kg: Decimal,
    transaction_type: InventoryTransactionType,
    source_type: str,
    source_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
    notes: str | None = None,
) -> InventoryTransaction:
    """Append a stock movement. Refuses a zero movement or one that would make the
    balance negative. Does not commit — the caller owns the transaction boundary.
    """
    if quantity_kg == 0:
        raise DomainError("Inventory movement quantity cannot be zero")

    if quantity_kg < 0:
        current = available_quantity(db, item_type, item_id)
        if current + quantity_kg < 0:
            raise InsufficientStockError(
                f"Insufficient stock: available {current}, requested {-quantity_kg}"
            )

    txn = InventoryTransaction(
        item_type=str(item_type),
        item_id=item_id,
        quantity_kg=quantity_kg,
        transaction_type=str(transaction_type),
        source_type=source_type,
        source_id=source_id,
        created_by=created_by,
        notes=notes,
    )
    db.add(txn)
    db.flush()
    return txn
