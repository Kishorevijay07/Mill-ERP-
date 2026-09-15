"""Settings models: the mill profile (singleton) and configurable charge rates.

Charge rates drive claim line generation (docs/UI-UX-SPEC Settings). Rates use
NUMERIC — never float. The mill profile is a single row; the service treats it as
a get-or-create singleton.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, Numeric, String, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import (
    AuditActorMixin,
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ChargeUnit(StrEnum):
    PER_KG = "PER_KG"
    PER_QUINTAL = "PER_QUINTAL"  # 100 kg
    FLAT = "FLAT"


class MillSettings(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "mill_settings"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    registration_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    invoice_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # GST tax-invoice identity (seller block + tax invoice bank/declaration).
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(4), nullable=True)
    bank_account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bank_account_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_branch: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(16), nullable=True)
    invoice_declaration: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class ChargeRate(UUIDPrimaryKeyMixin, TimestampMixin, AuditActorMixin, Base):
    __tablename__ = "charge_rates"
    __table_args__ = (CheckConstraint("rate >= 0", name="rate_non_negative"),)

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default=ChargeUnit.PER_KG)
    is_deduction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
