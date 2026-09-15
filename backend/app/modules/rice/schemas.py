"""Pydantic schemas for the rice QC and rice-lot API."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QualityDecision(BaseModel):
    broken_pct: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    moisture_pct: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    notes: str | None = Field(default=None, max_length=1000)


class RiceQualityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    output_id: uuid.UUID
    status: str
    broken_pct: Decimal | None
    moisture_pct: Decimal | None
    notes: str | None
    created_at: datetime


class RiceLotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    output_id: uuid.UUID
    category: str
    quantity_kg: Decimal
    bag_weight_kg: Decimal
    bag_count: int
    created_at: datetime


class RiceLotWithStock(RiceLotOut):
    available_kg: Decimal


class QCPassResponse(BaseModel):
    quality: RiceQualityOut
    rice_lot: RiceLotOut
