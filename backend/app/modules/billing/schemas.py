"""Pydantic schemas for the billing API (claims, lines, payments)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    agency_id: uuid.UUID
    delivery_receipt_ids: list[uuid.UUID] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)


class ClaimLineInput(BaseModel):
    description: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(ge=0, max_digits=14, decimal_places=3)
    rate: Decimal = Field(ge=0, max_digits=14, decimal_places=4)
    is_deduction: bool = False


class ClaimLinesReplace(BaseModel):
    lines: list[ClaimLineInput]


class ClaimLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    quantity: Decimal
    rate: Decimal
    amount: Decimal
    is_deduction: bool
    sort_order: int


class PaymentCreate(BaseModel):
    claim_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_on: date | None = None
    method: str | None = Field(default=None, max_length=64)
    reference_no: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=1000)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    claim_id: uuid.UUID
    amount: Decimal
    paid_on: date | None
    method: str | None
    reference_no: str | None
    notes: str | None
    created_at: datetime


class ClaimOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    agency_id: uuid.UUID
    status: str
    currency: str
    gross_amount: Decimal
    deduction_amount: Decimal
    net_amount: Decimal
    submitted_at: datetime | None
    approved_at: datetime | None
    notes: str | None
    created_at: datetime


class ClaimDetail(ClaimOut):
    lines: list[ClaimLineOut]
    delivery_receipt_ids: list[uuid.UUID]
    payments: list[PaymentOut]
    paid_amount: Decimal
    outstanding_amount: Decimal


class InvoiceResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
