"""Pydantic schemas for the dispatch & delivery API."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DispatchItemCreate(BaseModel):
    rice_lot_id: uuid.UUID
    quantity_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)


class DispatchCreate(BaseModel):
    destination_name: str = Field(min_length=1, max_length=255)
    lorry_number: str = Field(min_length=1, max_length=32)
    items: list[DispatchItemCreate] = Field(min_length=1)
    destination_agency_id: uuid.UUID | None = None
    delivery_order_id: uuid.UUID | None = None
    notes: str | None = Field(default=None, max_length=1000)


class DeliveryReceiptCreate(BaseModel):
    received_quantity_kg: Decimal = Field(ge=0, max_digits=14, decimal_places=3)
    received_bags: int | None = Field(default=None, ge=0)
    receipt_number: str | None = Field(default=None, max_length=64)
    receipt_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class DispatchItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rice_lot_id: uuid.UUID
    quantity_kg: Decimal


class DeliveryReceiptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    dispatch_id: uuid.UUID
    dispatched_quantity_kg: Decimal
    received_quantity_kg: Decimal
    received_bags: int | None
    shortage_kg: Decimal
    excess_kg: Decimal
    receipt_number: str | None
    receipt_date: date | None
    notes: str | None
    created_at: datetime


class DispatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    status: str
    destination_name: str
    destination_agency_id: uuid.UUID | None
    delivery_order_id: uuid.UUID | None
    lorry_number: str
    dispatched_at: datetime | None
    notes: str | None
    created_at: datetime


class DispatchDetail(DispatchOut):
    items: list[DispatchItemOut]
    receipt: DeliveryReceiptOut | None
