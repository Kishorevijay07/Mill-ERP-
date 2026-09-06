"""Rice domain models: quality control and rice lots.

Each RiceProductionOutput has one RiceQuality (PENDING -> PASSED | FAILED).
Passing QC creates a RiceLot (1:1 with the output) and posts a positive rice
inventory movement — the only way rice stock is created. Rice that fails QC
never becomes a lot and so can never be dispatched.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_QTY = Numeric(14, 3)
_BAG = Numeric(10, 3)
_PCT = Numeric(5, 2)


class RiceQualityStatus(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class RiceQuality(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "rice_quality"
    __table_args__ = (
        CheckConstraint(
            "broken_pct IS NULL OR (broken_pct >= 0 AND broken_pct <= 100)",
            name="broken_range",
        ),
        CheckConstraint(
            "moisture_pct IS NULL OR (moisture_pct >= 0 AND moisture_pct <= 100)",
            name="moisture_range",
        ),
    )

    # 1:1 with a rice production output.
    output_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rice_production_outputs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=RiceQualityStatus.PENDING,
        server_default=text(f"'{RiceQualityStatus.PENDING}'"),
        index=True,
    )
    broken_pct: Mapped[Decimal | None] = mapped_column(_PCT, nullable=True)
    moisture_pct: Mapped[Decimal | None] = mapped_column(_PCT, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class RiceLot(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "rice_lots"
    __table_args__ = (
        CheckConstraint("quantity_kg > 0", name="quantity_positive"),
        CheckConstraint("bag_weight_kg > 0", name="bag_weight_positive"),
        CheckConstraint("bag_count >= 0", name="bag_count_non_negative"),
    )

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # 1:1 with the passed output.
    output_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rice_production_outputs.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    bag_weight_kg: Mapped[Decimal] = mapped_column(_BAG, nullable=False)
    bag_count: Mapped[int] = mapped_column(Integer, nullable=False)
