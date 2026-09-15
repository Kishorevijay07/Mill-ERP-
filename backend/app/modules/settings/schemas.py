"""Pydantic schemas for settings (mill profile + charge rates)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.settings.models import ChargeUnit


class MillSettingsUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str | None = Field(default=None, max_length=1000)
    registration_no: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    contact_email: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="INR", min_length=1, max_length=8)
    invoice_notes: str | None = Field(default=None, max_length=2000)
    gstin: str | None = Field(default=None, max_length=20)
    state_name: str | None = Field(default=None, max_length=64)
    state_code: str | None = Field(default=None, max_length=4)
    bank_account_name: str | None = Field(default=None, max_length=255)
    bank_name: str | None = Field(default=None, max_length=128)
    bank_account_no: str | None = Field(default=None, max_length=64)
    bank_branch: str | None = Field(default=None, max_length=128)
    bank_ifsc: str | None = Field(default=None, max_length=16)
    invoice_declaration: str | None = Field(default=None, max_length=1000)


class MillSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str | None
    registration_no: str | None
    contact_phone: str | None
    contact_email: str | None
    currency: str
    invoice_notes: str | None
    gstin: str | None
    state_name: str | None
    state_code: str | None
    bank_account_name: str | None
    bank_name: str | None
    bank_account_no: str | None
    bank_branch: str | None
    bank_ifsc: str | None
    invoice_declaration: str | None


class ChargeRateCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    rate: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    unit: ChargeUnit = ChargeUnit.PER_KG
    is_deduction: bool = False
    is_active: bool = True


class ChargeRateUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    rate: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    unit: ChargeUnit
    is_deduction: bool
    is_active: bool


class ChargeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    label: str
    rate: Decimal
    unit: str
    is_deduction: bool
    is_active: bool
