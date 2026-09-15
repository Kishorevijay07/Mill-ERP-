"""Pydantic schemas for the milling API."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.milling.models import RiceCategory


class MillingInputCreate(BaseModel):
    paddy_lot_id: uuid.UUID
    quantity_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)


class MillingBatchCreate(BaseModel):
    inputs: list[MillingInputCreate] = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)


class OutputCreate(BaseModel):
    category: RiceCategory
    quantity_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    bag_weight_kg: Decimal = Field(gt=0, max_digits=10, decimal_places=3)


class ProductionCreate(BaseModel):
    outputs: list[OutputCreate] = Field(min_length=1)
    produced_on: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class MillingInputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paddy_lot_id: uuid.UUID
    quantity_kg: Decimal


class RiceProductionOutputOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    quantity_kg: Decimal
    bag_weight_kg: Decimal
    bag_count: int


class RiceProductionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    produced_on: date | None
    notes: str | None
    outputs: list[RiceProductionOutputOut]


class MillingBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime


class MillingBatchDetail(MillingBatchOut):
    inputs: list[MillingInputOut]
    productions: list[RiceProductionOut]
