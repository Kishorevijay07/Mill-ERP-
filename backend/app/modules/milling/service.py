"""Milling domain logic: batches, paddy consumption, and rice production.

Key invariants:
- Starting a batch consumes paddy atomically: each paddy lot row is locked
  (SELECT ... FOR UPDATE), its available balance is checked, and a negative
  inventory movement is posted. Concurrent milling of the same lot is therefore
  serialized and cannot overspend stock.
- Rice production is recorded only while a batch is IN_PROGRESS. Each output gets
  a PENDING rice-quality record; rice stock is not created until QC passes.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import InventoryItemType, InventoryTransactionType
from app.modules.milling.models import (
    MillingBatch,
    MillingBatchStatus,
    MillingInput,
    RiceProduction,
    RiceProductionOutput,
)
from app.modules.milling.schemas import MillingBatchCreate, ProductionCreate
from app.modules.receiving.models import PaddyLot
from app.modules.rice.models import RiceQuality
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

_BATCH_ENTITY = "milling_batch"


def _now() -> datetime:
    return datetime.now(UTC)


def _get_batch(db: Session, batch_id: uuid.UUID) -> MillingBatch:
    batch = db.get(MillingBatch, batch_id)
    if batch is None:
        raise NotFoundError("Milling batch not found")
    return batch


def create_batch(db: Session, data: MillingBatchCreate, actor: ActorContext) -> MillingBatch:
    # Validate all referenced paddy lots exist before creating anything.
    for item in data.inputs:
        if db.get(PaddyLot, item.paddy_lot_id) is None:
            raise NotFoundError(f"Paddy lot {item.paddy_lot_id} not found")

    reference = generate_reference(db, ReferencePrefix.MILLING_BATCH)
    batch = MillingBatch(
        reference=reference,
        status=MillingBatchStatus.DRAFT,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(batch)
    db.flush()
    for item in data.inputs:
        db.add(
            MillingInput(
                batch_id=batch.id,
                paddy_lot_id=item.paddy_lot_id,
                quantity_kg=item.quantity_kg,
                created_by=actor.user_id,
                updated_by=actor.user_id,
            )
        )
    record_audit(
        db,
        action="milling_batch.create",
        entity_type=_BATCH_ENTITY,
        entity_id=batch.id,
        entity_reference=batch.reference,
        user_id=actor.user_id,
        after_data={"status": batch.status, "inputs": len(data.inputs)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _get_batch_loaded(db, batch.id)


def _get_batch_loaded(db: Session, batch_id: uuid.UUID) -> MillingBatch:
    batch = db.execute(
        select(MillingBatch)
        .options(
            selectinload(MillingBatch.inputs),
            selectinload(MillingBatch.productions).selectinload(RiceProduction.outputs),
        )
        .where(MillingBatch.id == batch_id)
    ).scalar_one_or_none()
    if batch is None:
        raise NotFoundError("Milling batch not found")
    return batch


def get_batch(db: Session, batch_id: uuid.UUID) -> MillingBatch:
    return _get_batch_loaded(db, batch_id)


def list_batches(db: Session, page: int, page_size: int) -> tuple[list[MillingBatch], int]:
    total = db.execute(select(func.count()).select_from(MillingBatch)).scalar_one()
    rows = list(
        db.execute(
            select(MillingBatch)
            .order_by(MillingBatch.reference)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()
    )
    return rows, total


def start_batch(db: Session, batch_id: uuid.UUID, actor: ActorContext) -> MillingBatch:
    """DRAFT -> IN_PROGRESS, consuming each input's paddy from inventory."""
    batch = _get_batch(db, batch_id)
    if batch.status != MillingBatchStatus.DRAFT:
        raise InvalidStateError(f"Batch {batch.reference} cannot start from status {batch.status}")

    inputs = list(
        db.execute(select(MillingInput).where(MillingInput.batch_id == batch_id)).scalars()
    )
    if not inputs:
        raise InvalidStateError("Batch has no paddy inputs")

    for item in inputs:
        # Lock the lot row so concurrent batches cannot overspend the same lot.
        db.get(PaddyLot, item.paddy_lot_id, with_for_update=True)
        inventory_service.post_transaction(
            db,
            item_type=InventoryItemType.PADDY_LOT,
            item_id=item.paddy_lot_id,
            quantity_kg=-item.quantity_kg,
            transaction_type=InventoryTransactionType.PADDY_CONSUMPTION,
            source_type=_BATCH_ENTITY,
            source_id=batch.id,
            created_by=actor.user_id,
            notes=f"Consumed by {batch.reference}",
        )

    batch.status = MillingBatchStatus.IN_PROGRESS
    batch.started_at = _now()
    batch.updated_by = actor.user_id
    record_audit(
        db,
        action="milling_batch.start",
        entity_type=_BATCH_ENTITY,
        entity_id=batch.id,
        entity_reference=batch.reference,
        user_id=actor.user_id,
        before_data={"status": MillingBatchStatus.DRAFT},
        after_data={"status": batch.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _get_batch_loaded(db, batch_id)


def record_production(
    db: Session, batch_id: uuid.UUID, data: ProductionCreate, actor: ActorContext
) -> RiceProduction:
    batch = _get_batch(db, batch_id)
    if batch.status != MillingBatchStatus.IN_PROGRESS:
        raise InvalidStateError(f"Batch {batch.reference} must be in progress to record production")

    reference = generate_reference(db, ReferencePrefix.RICE_PRODUCTION)
    production = RiceProduction(
        reference=reference,
        batch_id=batch_id,
        produced_on=data.produced_on,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(production)
    db.flush()

    for out in data.outputs:
        bag_count = int(out.quantity_kg // out.bag_weight_kg)
        output = RiceProductionOutput(
            production_id=production.id,
            category=out.category,
            quantity_kg=out.quantity_kg,
            bag_weight_kg=out.bag_weight_kg,
            bag_count=bag_count,
            created_by=actor.user_id,
            updated_by=actor.user_id,
        )
        db.add(output)
        db.flush()
        # Each output awaits QC before it can become stock.
        db.add(RiceQuality(output_id=output.id, created_by=actor.user_id))

    record_audit(
        db,
        action="rice_production.record",
        entity_type="rice_production",
        entity_id=production.id,
        entity_reference=production.reference,
        user_id=actor.user_id,
        after_data={"batch": batch.reference, "outputs": len(data.outputs)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return db.execute(
        select(RiceProduction)
        .options(selectinload(RiceProduction.outputs))
        .where(RiceProduction.id == production.id)
    ).scalar_one()


def complete_batch(db: Session, batch_id: uuid.UUID, actor: ActorContext) -> MillingBatch:
    batch = _get_batch(db, batch_id)
    if batch.status != MillingBatchStatus.IN_PROGRESS:
        raise InvalidStateError(
            f"Batch {batch.reference} cannot complete from status {batch.status}"
        )

    output_count = db.execute(
        select(func.count())
        .select_from(RiceProductionOutput)
        .join(RiceProduction, RiceProductionOutput.production_id == RiceProduction.id)
        .where(RiceProduction.batch_id == batch_id)
    ).scalar_one()
    if output_count == 0:
        raise InvalidStateError("Batch has no recorded production output")

    batch.status = MillingBatchStatus.COMPLETED
    batch.completed_at = _now()
    batch.updated_by = actor.user_id
    record_audit(
        db,
        action="milling_batch.complete",
        entity_type=_BATCH_ENTITY,
        entity_id=batch.id,
        entity_reference=batch.reference,
        user_id=actor.user_id,
        before_data={"status": MillingBatchStatus.IN_PROGRESS},
        after_data={"status": batch.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _get_batch_loaded(db, batch_id)


def available_paddy(db: Session, paddy_lot_id: uuid.UUID) -> Decimal:
    return inventory_service.available_quantity(db, InventoryItemType.PADDY_LOT, paddy_lot_id)
