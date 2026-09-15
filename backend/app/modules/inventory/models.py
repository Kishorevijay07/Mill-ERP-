"""Inventory: the authoritative, append-only stock-movement ledger.

Stock is never edited directly (docs/DEVELOPMENT-RULES.md). Every change is an
``InventoryTransaction`` row with a signed quantity (+ receipt, - consumption)
that references the lot it moves and the business transaction that caused it.
Available stock for a lot is the sum of its movements.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base, UUIDPrimaryKeyMixin


class InventoryItemType(StrEnum):
    PADDY_LOT = "PADDY_LOT"
    RICE_LOT = "RICE_LOT"


class InventoryTransactionType(StrEnum):
    PADDY_RECEIPT = "PADDY_RECEIPT"
    PADDY_CONSUMPTION = "PADDY_CONSUMPTION"
    RICE_PRODUCTION = "RICE_PRODUCTION"
    RICE_DISPATCH = "RICE_DISPATCH"
    REVERSAL = "REVERSAL"


class InventoryTransaction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (Index("ix_inventory_transactions_item", "item_type", "item_id"),)

    item_type: Mapped[str] = mapped_column(String(16), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid(), nullable=False)
    # Signed quantity in kilograms: positive adds stock, negative consumes it.
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # The business transaction that caused this movement (e.g. a government load).
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
