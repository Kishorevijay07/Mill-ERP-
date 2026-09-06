"""Pydantic schemas for the government receiving API."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# Government agency
# --------------------------------------------------------------------------- #
class AgencyCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=32)


class AgencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    contact_name: str | None
    contact_phone: str | None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Allocation
# --------------------------------------------------------------------------- #
class AllocationCreate(BaseModel):
    agency_id: uuid.UUID
    quantity_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    allocated_on: date
    season: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)


class AllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    agency_id: uuid.UUID
    quantity_kg: Decimal
    allocated_on: date
    season: str | None
    notes: str | None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Delivery order
# --------------------------------------------------------------------------- #
class DeliveryOrderCreate(BaseModel):
    allocation_id: uuid.UUID
    do_number: str = Field(min_length=1, max_length=64)
    quantity_kg: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    issued_on: date
    notes: str | None = Field(default=None, max_length=1000)


class DeliveryOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    allocation_id: uuid.UUID
    do_number: str
    quantity_kg: Decimal
    issued_on: date
    notes: str | None
    created_at: datetime


# --------------------------------------------------------------------------- #
# Government load
# --------------------------------------------------------------------------- #
class LoadCreate(BaseModel):
    delivery_order_id: uuid.UUID
    lorry_number: str = Field(min_length=1, max_length=32)
    driver_name: str | None = Field(default=None, max_length=255)
    declared_quantity_kg: Decimal | None = Field(
        default=None, gt=0, max_digits=14, decimal_places=3
    )
    notes: str | None = Field(default=None, max_length=1000)


class LoadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reference: str
    delivery_order_id: uuid.UUID
    lorry_number: str
    driver_name: str | None
    declared_quantity_kg: Decimal | None
    status: str
    notes: str | None
    created_at: datetime
