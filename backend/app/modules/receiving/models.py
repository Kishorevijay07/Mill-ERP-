"""Receiving domain models: weighment, paddy quality, and paddy lot.

Relationships (docs/DOMAIN-MODEL.md, Phase 1):
- GovernmentLoad 1:N Weighment, with exactly one authoritative ``is_final`` row.
- GovernmentLoad 1:1 PaddyQuality.
- GovernmentLoad 1:1 PaddyLot (created only on acceptance).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_QTY = Numeric(14, 3)
_PCT = Numeric(5, 2)


class Weighment(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "weighments"
    __table_args__ = (
        CheckConstraint("gross_kg > 0", name="gross_positive"),
        CheckConstraint("tare_kg >= 0", name="tare_non_negative"),
        CheckConstraint("gross_kg > tare_kg", name="gross_gt_tare"),
        CheckConstraint("net_kg > 0", name="net_positive"),
        Index("ix_weighments_load_id", "load_id"),
    )

    load_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_loads.id", ondelete="CASCADE"), nullable=False
    )
    gross_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    tare_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    # net_kg = gross_kg - tare_kg, computed server-side.
    net_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    # The authoritative weighment for the load. Exactly one per load (enforced in
    # the service; superseded weighments are kept for history).
    is_final: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=false()
    )
    weighbridge_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PaddyQuality(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "paddy_quality"
    __table_args__ = (
        CheckConstraint("moisture_pct >= 0 AND moisture_pct <= 100", name="moisture_range"),
        CheckConstraint(
            "foreign_matter_pct >= 0 AND foreign_matter_pct <= 100",
            name="foreign_matter_range",
        ),
        CheckConstraint("damaged_pct >= 0 AND damaged_pct <= 100", name="damaged_range"),
    )

    # 1:1 with the load.
    load_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_loads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    moisture_pct: Mapped[Decimal] = mapped_column(_PCT, nullable=False)
    foreign_matter_pct: Mapped[Decimal] = mapped_column(_PCT, nullable=False)
    damaged_pct: Mapped[Decimal] = mapped_column(_PCT, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class PaddyLot(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "paddy_lots"
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="quantity_positive"),)

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # 1:1 with the accepted load.
    load_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_loads.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    # Original received quantity. Available quantity is derived from inventory.
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
