"""Billing models: government claims, claim lines, claim-delivery links, payments.

A claim bills a government agency for delivered rice. It covers one or more
delivery receipts (each receipt claimable at most once), carries charge/deduction
lines, and server-computed gross/deduction/net totals. Payments reduce the
outstanding balance until PAID. All money is NUMERIC(14,2) — never float.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

_MONEY = Numeric(14, 2)
_QTY = Numeric(14, 3)
_RATE = Numeric(14, 4)


class ClaimStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"


class GovernmentClaim(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "government_claims"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="gross_non_negative"),
        CheckConstraint("deduction_amount >= 0", name="deduction_non_negative"),
        CheckConstraint("net_amount >= 0", name="net_non_negative"),
    )

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_agencies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=ClaimStatus.DRAFT,
        server_default=text(f"'{ClaimStatus.DRAFT}'"),
        index=True,
    )
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    gross_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0"))
    deduction_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0"))
    net_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    lines: Mapped[list[ClaimLine]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    deliveries: Mapped[list[ClaimDelivery]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimDelivery(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "claim_deliveries"

    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Unique across the table: a delivery receipt can be claimed at most once.
    delivery_receipt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("delivery_receipts.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    claim: Mapped[GovernmentClaim] = relationship(back_populates="deliveries")


class ClaimLine(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "claim_lines"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("rate >= 0", name="rate_non_negative"),
    )

    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(_QTY, nullable=False)
    rate: Mapped[Decimal] = mapped_column(_RATE, nullable=False)
    amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)
    is_deduction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    claim: Mapped[GovernmentClaim] = relationship(back_populates="lines")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("government_claims.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)
    paid_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    claim: Mapped[GovernmentClaim] = relationship(back_populates="payments")
