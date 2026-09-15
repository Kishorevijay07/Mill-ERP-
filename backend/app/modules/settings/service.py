"""Settings domain logic: mill profile (singleton) and charge-rate management."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.settings.models import ChargeRate, MillSettings
from app.modules.settings.schemas import (
    ChargeRateCreate,
    ChargeRateUpdate,
    MillSettingsUpdate,
)
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, NotFoundError

_DEFAULT_MILL_NAME = "Rice Mill"


def get_or_create_mill_settings(db: Session, actor: ActorContext | None = None) -> MillSettings:
    settings = db.execute(select(MillSettings)).scalars().first()
    if settings is None:
        settings = MillSettings(
            name=_DEFAULT_MILL_NAME,
            currency="INR",
            created_by=actor.user_id if actor else None,
            updated_by=actor.user_id if actor else None,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_mill_settings(
    db: Session, data: MillSettingsUpdate, actor: ActorContext
) -> MillSettings:
    settings = get_or_create_mill_settings(db, actor)
    settings.name = data.name
    settings.address = data.address
    settings.registration_no = data.registration_no
    settings.contact_phone = data.contact_phone
    settings.contact_email = data.contact_email
    settings.currency = data.currency
    settings.invoice_notes = data.invoice_notes
    settings.gstin = data.gstin
    settings.state_name = data.state_name
    settings.state_code = data.state_code
    settings.bank_account_name = data.bank_account_name
    settings.bank_name = data.bank_name
    settings.bank_account_no = data.bank_account_no
    settings.bank_branch = data.bank_branch
    settings.bank_ifsc = data.bank_ifsc
    settings.invoice_declaration = data.invoice_declaration
    settings.updated_by = actor.user_id
    record_audit(
        db,
        action="mill_settings.update",
        entity_type="mill_settings",
        entity_id=settings.id,
        user_id=actor.user_id,
        after_data={"name": settings.name, "currency": settings.currency},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(settings)
    return settings


def list_charge_rates(db: Session, active_only: bool = False) -> list[ChargeRate]:
    stmt = select(ChargeRate).order_by(ChargeRate.code)
    if active_only:
        stmt = stmt.where(ChargeRate.is_active.is_(True))
    return list(db.execute(stmt).scalars())


def create_charge_rate(db: Session, data: ChargeRateCreate, actor: ActorContext) -> ChargeRate:
    if (
        db.execute(select(ChargeRate).where(ChargeRate.code == data.code)).scalar_one_or_none()
        is not None
    ):
        raise ConflictError(f"Charge rate '{data.code}' already exists")
    rate = ChargeRate(
        code=data.code,
        label=data.label,
        rate=data.rate,
        unit=data.unit,
        is_deduction=data.is_deduction,
        is_active=data.is_active,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(rate)
    record_audit(
        db,
        action="charge_rate.create",
        entity_type="charge_rate",
        entity_id=None,
        entity_reference=data.code,
        user_id=actor.user_id,
        after_data={"code": data.code, "rate": str(data.rate)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(rate)
    return rate


def update_charge_rate(
    db: Session, rate_id: uuid.UUID, data: ChargeRateUpdate, actor: ActorContext
) -> ChargeRate:
    rate = db.get(ChargeRate, rate_id)
    if rate is None:
        raise NotFoundError("Charge rate not found")
    rate.label = data.label
    rate.rate = data.rate
    rate.unit = data.unit
    rate.is_deduction = data.is_deduction
    rate.is_active = data.is_active
    rate.updated_by = actor.user_id
    record_audit(
        db,
        action="charge_rate.update",
        entity_type="charge_rate",
        entity_id=rate.id,
        entity_reference=rate.code,
        user_id=actor.user_id,
        after_data={"rate": str(data.rate), "is_active": data.is_active},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(rate)
    return rate


def delete_charge_rate(db: Session, rate_id: uuid.UUID, actor: ActorContext) -> None:
    rate = db.get(ChargeRate, rate_id)
    if rate is None:
        raise NotFoundError("Charge rate not found")
    record_audit(
        db,
        action="charge_rate.delete",
        entity_type="charge_rate",
        entity_id=rate.id,
        entity_reference=rate.code,
        user_id=actor.user_id,
        before_data={"code": rate.code},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.delete(rate)
    db.commit()


def seed_default_charge_rates(db: Session) -> None:
    """Idempotently seed a couple of default charge rates for a fresh mill."""
    defaults = [
        ("MILLING", "Milling charge", "1.5000", "PER_KG", False),
        ("HANDLING", "Handling & bagging", "0.5000", "PER_KG", False),
        ("GUNNY_DEDUCTION", "Gunny deduction", "0.1000", "PER_KG", True),
    ]
    for code, label, rate, unit, is_deduction in defaults:
        existing = db.execute(
            select(ChargeRate).where(ChargeRate.code == code)
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                ChargeRate(
                    code=code,
                    label=label,
                    rate=rate,
                    unit=unit,
                    is_deduction=is_deduction,
                    is_active=True,
                )
            )
    db.commit()
