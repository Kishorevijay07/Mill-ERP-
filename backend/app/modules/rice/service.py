"""Rice QC and rice-lot logic.

Passing QC is the sole path to rice stock: it creates a RiceLot (1:1 with the
output) and posts a positive rice inventory movement, atomically. Failing QC
records the decision but creates no lot and no stock, so failed rice can never be
dispatched.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import InventoryItemType, InventoryTransactionType
from app.modules.milling.models import RiceProductionOutput
from app.modules.rice.models import RiceLot, RiceQuality, RiceQualityStatus
from app.modules.rice.schemas import QualityDecision
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

_QUALITY_ENTITY = "rice_quality"


def _get_quality(db: Session, quality_id: uuid.UUID) -> RiceQuality:
    quality = db.get(RiceQuality, quality_id)
    if quality is None:
        raise NotFoundError("Rice quality record not found")
    return quality


def list_quality(
    db: Session, status: str | None, page: int, page_size: int
) -> tuple[list[RiceQuality], int]:
    stmt = select(RiceQuality)
    count_stmt = select(func.count()).select_from(RiceQuality)
    if status is not None:
        stmt = stmt.where(RiceQuality.status == status)
        count_stmt = count_stmt.where(RiceQuality.status == status)
    total = db.execute(count_stmt).scalar_one()
    rows = list(
        db.execute(
            stmt.order_by(RiceQuality.created_at).offset((page - 1) * page_size).limit(page_size)
        ).scalars()
    )
    return rows, total


def get_quality(db: Session, quality_id: uuid.UUID) -> RiceQuality:
    return _get_quality(db, quality_id)


def pass_quality(
    db: Session, quality_id: uuid.UUID, data: QualityDecision, actor: ActorContext
) -> tuple[RiceQuality, RiceLot]:
    quality = _get_quality(db, quality_id)
    if quality.status != RiceQualityStatus.PENDING:
        raise InvalidStateError(f"Quality is already {quality.status} and cannot be changed")

    output = db.get(RiceProductionOutput, quality.output_id)
    if output is None:
        raise NotFoundError("Rice production output not found")

    if (
        db.execute(select(RiceLot).where(RiceLot.output_id == output.id)).scalar_one_or_none()
        is not None
    ):
        raise ConflictError("A rice lot already exists for this output")

    quality.status = RiceQualityStatus.PASSED
    quality.broken_pct = data.broken_pct
    quality.moisture_pct = data.moisture_pct
    quality.notes = data.notes
    quality.updated_by = actor.user_id

    reference = generate_reference(db, ReferencePrefix.RICE_LOT)
    rice_lot = RiceLot(
        reference=reference,
        output_id=output.id,
        category=output.category,
        quantity_kg=output.quantity_kg,
        bag_weight_kg=output.bag_weight_kg,
        bag_count=output.bag_count,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(rice_lot)
    db.flush()

    inventory_service.post_transaction(
        db,
        item_type=InventoryItemType.RICE_LOT,
        item_id=rice_lot.id,
        quantity_kg=output.quantity_kg,
        transaction_type=InventoryTransactionType.RICE_PRODUCTION,
        source_type="rice_production_output",
        source_id=output.id,
        created_by=actor.user_id,
        notes=f"Rice produced ({rice_lot.reference})",
    )

    record_audit(
        db,
        action="rice_quality.pass",
        entity_type=_QUALITY_ENTITY,
        entity_id=quality.id,
        entity_reference=rice_lot.reference,
        user_id=actor.user_id,
        after_data={
            "status": quality.status,
            "rice_lot": rice_lot.reference,
            "quantity_kg": str(rice_lot.quantity_kg),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(quality)
    db.refresh(rice_lot)
    return quality, rice_lot


def fail_quality(
    db: Session, quality_id: uuid.UUID, data: QualityDecision, actor: ActorContext
) -> RiceQuality:
    quality = _get_quality(db, quality_id)
    if quality.status != RiceQualityStatus.PENDING:
        raise InvalidStateError(f"Quality is already {quality.status} and cannot be changed")
    quality.status = RiceQualityStatus.FAILED
    quality.broken_pct = data.broken_pct
    quality.moisture_pct = data.moisture_pct
    quality.notes = data.notes
    quality.updated_by = actor.user_id
    record_audit(
        db,
        action="rice_quality.fail",
        entity_type=_QUALITY_ENTITY,
        entity_id=quality.id,
        user_id=actor.user_id,
        after_data={"status": quality.status, "notes": data.notes},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(quality)
    return quality


def list_rice_lots(db: Session) -> list[tuple[RiceLot, Decimal]]:
    lots = list(db.execute(select(RiceLot).order_by(RiceLot.reference)).scalars())
    return [
        (lot, inventory_service.available_quantity(db, InventoryItemType.RICE_LOT, lot.id))
        for lot in lots
    ]


def get_rice_lot(db: Session, lot_id: uuid.UUID) -> tuple[RiceLot, Decimal]:
    lot = db.get(RiceLot, lot_id)
    if lot is None:
        raise NotFoundError("Rice lot not found")
    available = inventory_service.available_quantity(db, InventoryItemType.RICE_LOT, lot.id)
    return lot, available
