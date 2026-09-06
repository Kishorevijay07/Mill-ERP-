"""Milling domain models: batches, inputs, productions, and outputs.

Chain (docs/DOMAIN-MODEL.md):
    MillingBatch N:M PaddyLot (via MillingInput)
    MillingBatch 1:N RiceProduction 1:N RiceProductionOutput

A batch consumes paddy when it *starts* (DRAFT -> IN_PROGRESS): each input posts
a negative paddy inventory movement. Rice production is recorded while the batch
is IN_PROGRESS. Rice stock is not created here — it appears only when a rice lot
is created from an output that passes QC (see the ``rice`` module).
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
_BAG = Numeric(10, 3)


class MillingBatchStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RiceCategory(StrEnum):
    # Two categories for Phase 1; naming them is a future settings concern.
    CATEGORY_1 = "CATEGORY_1"
    CATEGORY_2 = "CATEGORY_2"


class MillingBatch(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "milling_batches"

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=MillingBatchStatus.DRAFT,
        server_default=text(f"'{MillingBatchStatus.DRAFT}'"),
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    inputs: Mapped[list[MillingInput]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
    productions: Mapped[list[RiceProduction]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class MillingInput(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "milling_inputs"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="quantity_positive"),
        UniqueConstraint("batch_id", "paddy_lot_id", name="batch_paddy_lot"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milling_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paddy_lot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("paddy_lots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)

    batch: Mapped[MillingBatch] = relationship(back_populates="inputs")


class RiceProduction(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "rice_productions"

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("milling_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    produced_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    batch: Mapped[MillingBatch] = relationship(back_populates="productions")
    outputs: Mapped[list[RiceProductionOutput]] = relationship(
        back_populates="production", cascade="all, delete-orphan"
    )


class RiceProductionOutput(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "rice_production_outputs"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="quantity_positive"),
        CheckConstraint("bag_weight_kg > 0", name="bag_weight_positive"),
        CheckConstraint("bag_count >= 0", name="bag_count_non_negative"),
    )

    production_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rice_productions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    bag_weight_kg: Mapped[Decimal] = mapped_column(_BAG, nullable=False)
    # Whole bags, computed server-side = floor(quantity_kg / bag_weight_kg).
    bag_count: Mapped[int] = mapped_column(Integer, nullable=False)

    production: Mapped[RiceProduction] = relationship(back_populates="outputs")
