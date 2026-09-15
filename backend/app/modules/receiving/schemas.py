"""Pydantic schemas for the receiving API."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.government.schemas import LoadOut


class WeighmentCreate(BaseModel):
    gross_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    tare_kg: Decimal = Field(ge=0, max_digits=14, decimal_places=3)
    weighbridge_ref: str | None = Field(default=None, max_length=64)


class WeighmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    load_id: uuid.UUID
    gross_kg: Decimal
    tare_kg: Decimal
    net_kg: Decimal
    is_final: bool
    weighbridge_ref: str | None
    created_at: datetime


class PaddyQualityCreate(BaseModel):
    moisture_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    foreign_matter_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    damaged_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)


class PaddyQualityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    load_id: uuid.UUID
    moisture_pct: Decimal
    foreign_matter_pct: Decimal
    damaged_pct: Decimal
    notes: str | None
    created_at: datetime


class PaddyLotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    load_id: uuid.UUID
    quantity_kg: Decimal
    created_at: datetime


class PaddyLotWithStock(PaddyLotOut):
    available_kg: Decimal


class RejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=1000)


class AcceptResponse(BaseModel):
    load: LoadOut
    paddy_lot: PaddyLotOut
