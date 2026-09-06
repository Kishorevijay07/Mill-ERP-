"""Government receiving domain models.

Chain (docs/DOMAIN-MODEL.md):
    GovernmentAgency 1:N Allocation 1:N DeliveryOrder 1:N GovernmentLoad

A GovernmentLoad carries the receiving state machine
(DRAFT -> ARRIVED -> WEIGHED -> QC_PENDING -> ACCEPTED | REJECTED). Transitions
requiring downstream records (weighment, QC) land with those modules; Stage 2
implements creation and the DRAFT -> ARRIVED transition.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

# Quantities are stored in kilograms with 3 decimal places — never float.
_QTY = Numeric(14, 3)


class LoadStatus(StrEnum):
    DRAFT = "DRAFT"
    ARRIVED = "ARRIVED"
    WEIGHED = "WEIGHED"
    QC_PENDING = "QC_PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class GovernmentAgency(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "government_agencies"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    allocations: Mapped[list[Allocation]] = relationship(back_populates="agency")


class Allocation(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "allocations"
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="quantity_positive"),)

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_agencies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    season: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    allocated_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    agency: Mapped[GovernmentAgency] = relationship(back_populates="allocations")
    delivery_orders: Mapped[list[DeliveryOrder]] = relationship(back_populates="allocation")


class DeliveryOrder(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "delivery_orders"
    __table_args__ = (CheckConstraint("quantity_kg > 0", name="quantity_positive"),)

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    allocation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("allocations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # The government's own DO number as printed on their paperwork.
    do_number: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_kg: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    allocation: Mapped[Allocation] = relationship(back_populates="delivery_orders")
    loads: Mapped[list[GovernmentLoad]] = relationship(back_populates="delivery_order")


class GovernmentLoad(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "government_loads"
    __table_args__ = (
        CheckConstraint(
            "declared_quantity_kg IS NULL OR declared_quantity_kg > 0",
            name="declared_quantity_positive",
        ),
    )

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    delivery_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("delivery_orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    lorry_number: Mapped[str] = mapped_column(String(32), nullable=False)
    driver_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    declared_quantity_kg: Mapped[Decimal | None] = mapped_column(_QTY, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=LoadStatus.DRAFT,
        server_default=text(f"'{LoadStatus.DRAFT}'"),
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    delivery_order: Mapped[DeliveryOrder] = relationship(back_populates="loads")
