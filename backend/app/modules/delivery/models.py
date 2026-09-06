"""Delivery domain models: dispatches, dispatch items, and delivery receipts.

Chain (docs/DOMAIN-MODEL.md):
    Dispatch N:M RiceLot (via DispatchItem)
    Dispatch 1:1 DeliveryReceipt (Phase 1: one final receipt + shortage/excess)

Rice stock is deducted when a dispatch transitions PREPARED -> DISPATCHED: each
item posts a negative rice inventory movement under a row lock. Rice that failed
QC never became a rice lot, so it can never appear as a dispatch item.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_QTY = Numeric(14, 3)


class DispatchStatus(StrEnum):
    DRAFT = "DRAFT"
    PREPARED = "PREPARED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"


class Dispatch(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "dispatches"

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=DispatchStatus.DRAFT,
        server_default=text(f"'{DispatchStatus.DRAFT}'"),
        index=True,
    )
    destination_name: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_agency_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("government_agencies.id", ondelete="RESTRICT"), nullable=True
    )
    # Optional link to the delivery order this dispatch fulfils (traceability).
    delivery_order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("delivery_orders.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    lorry_number: Mapped[str] = mapped_column(String(32), nullable=False)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    items: Mapped[list[DispatchItem]] = relationship(
        back_populates="dispatch", cascade="all, delete-orphan"
    )
    receipt: Mapped[DeliveryReceipt | None] = relationship(
        back_populates="dispatch", uselist=False, cascade="all, delete-orphan"
    )


class DispatchItem(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "dispatch_items"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="quantity_positive"),
        UniqueConstraint("dispatch_id", "rice_lot_id", name="dispatch_rice_lot"),
    )

    dispatch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rice_lot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rice_lots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)

    dispatch: Mapped[Dispatch] = relationship(back_populates="items")


class DeliveryReceipt(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "delivery_receipts"
    __table_args__ = (
        CheckConstraint("received_quantity_kg >= 0", name="received_non_negative"),
        CheckConstraint("shortage_kg >= 0", name="shortage_non_negative"),
        CheckConstraint("excess_kg >= 0", name="excess_non_negative"),
    )

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # 1:1 with the dispatch.
    dispatch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    dispatched_quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    received_quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    received_bags: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shortage_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    excess_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    receipt_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    dispatch: Mapped[Dispatch] = relationship(back_populates="receipt")
