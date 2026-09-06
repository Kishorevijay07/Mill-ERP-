"""Receiving domain logic: weighment, paddy QC, and the load accept/reject flow.

State machine (docs/BUSINESS-FLOW.md), each transition an explicit operation:

    ARRIVED --record_weighment--> WEIGHED
    WEIGHED --record_paddy_quality--> QC_PENDING
    QC_PENDING --accept--> ACCEPTED   (creates PaddyLot + inventory receipt)
    QC_PENDING --reject--> REJECTED

Business rules enforced here:
- A weighment must have gross > tare; net is computed server-side.
- A load cannot be accepted without a valid final weighment.
- A usable paddy lot is created only from an accepted load (1:1), and its
  received quantity posts a positive inventory movement — the only way paddy
  stock ever comes into existence.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.government.models import GovernmentLoad, LoadStatus
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import InventoryItemType, InventoryTransactionType
from app.modules.receiving.models import PaddyLot, PaddyQuality, Weighment
from app.modules.receiving.schemas import PaddyQualityCreate, WeighmentCreate
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

_LOAD_ENTITY = "government_load"


def _get_load(db: Session, load_id: uuid.UUID) -> GovernmentLoad:
    load = db.get(GovernmentLoad, load_id)
    if load is None:
        raise NotFoundError("Government load not found")
    return load


def _final_weighment(db: Session, load_id: uuid.UUID) -> Weighment | None:
    return db.execute(
        select(Weighment).where(Weighment.load_id == load_id, Weighment.is_final.is_(True))
    ).scalar_one_or_none()


# --------------------------------------------------------------------------- #
# Weighment  (ARRIVED -> WEIGHED)
# --------------------------------------------------------------------------- #
def record_weighment(
    db: Session, load_id: uuid.UUID, data: WeighmentCreate, actor: ActorContext
) -> Weighment:
    load = _get_load(db, load_id)
    if load.status not in (LoadStatus.ARRIVED, LoadStatus.WEIGHED):
        raise InvalidStateError(
            f"Load {load.reference} cannot be weighed from status {load.status}"
        )
    if data.gross_kg <= data.tare_kg:
        raise InvalidStateError("Gross weight must be greater than tare weight")

    net_kg = data.gross_kg - data.tare_kg

    # Supersede any previous final weighment; keep it for history.
    for previous in db.execute(
        select(Weighment).where(Weighment.load_id == load_id, Weighment.is_final.is_(True))
    ).scalars():
        previous.is_final = False

    weighment = Weighment(
        load_id=load_id,
        gross_kg=data.gross_kg,
        tare_kg=data.tare_kg,
        net_kg=net_kg,
        is_final=True,
        weighbridge_ref=data.weighbridge_ref,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(weighment)
    load.status = LoadStatus.WEIGHED
    load.updated_by = actor.user_id
    db.flush()
    record_audit(
        db,
        action="weighment.record",
        entity_type=_LOAD_ENTITY,
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        after_data={"net_kg": str(net_kg), "status": load.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(weighment)
    return weighment


def list_weighments(db: Session, load_id: uuid.UUID) -> list[Weighment]:
    _get_load(db, load_id)
    return list(
        db.execute(
            select(Weighment).where(Weighment.load_id == load_id).order_by(Weighment.created_at)
        ).scalars()
    )


# --------------------------------------------------------------------------- #
# Paddy quality  (WEIGHED -> QC_PENDING)
# --------------------------------------------------------------------------- #
def record_paddy_quality(
    db: Session, load_id: uuid.UUID, data: PaddyQualityCreate, actor: ActorContext
) -> PaddyQuality:
    load = _get_load(db, load_id)
    if load.status not in (LoadStatus.WEIGHED, LoadStatus.QC_PENDING):
        raise InvalidStateError(
            f"Load {load.reference} cannot record quality from status {load.status}"
        )

    quality = db.execute(
        select(PaddyQuality).where(PaddyQuality.load_id == load_id)
    ).scalar_one_or_none()
    if quality is None:
        quality = PaddyQuality(load_id=load_id, created_by=actor.user_id)
        db.add(quality)

    quality.moisture_pct = data.moisture_pct
    quality.foreign_matter_pct = data.foreign_matter_pct
    quality.damaged_pct = data.damaged_pct
    quality.notes = data.notes
    quality.updated_by = actor.user_id

    load.status = LoadStatus.QC_PENDING
    load.updated_by = actor.user_id
    db.flush()
    record_audit(
        db,
        action="paddy_quality.record",
        entity_type=_LOAD_ENTITY,
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        after_data={
            "moisture_pct": str(data.moisture_pct),
            "status": load.status,
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(quality)
    return quality


def get_paddy_quality(db: Session, load_id: uuid.UUID) -> PaddyQuality:
    _get_load(db, load_id)
    quality = db.execute(
        select(PaddyQuality).where(PaddyQuality.load_id == load_id)
    ).scalar_one_or_none()
    if quality is None:
        raise NotFoundError("Paddy quality not recorded for this load")
    return quality


# --------------------------------------------------------------------------- #
# Accept  (QC_PENDING -> ACCEPTED)  and  Reject  (QC_PENDING -> REJECTED)
# --------------------------------------------------------------------------- #
def accept_load(
    db: Session, load_id: uuid.UUID, actor: ActorContext
) -> tuple[GovernmentLoad, PaddyLot]:
    """Accept a load: create its paddy lot and post the paddy receipt to inventory.

    Atomic: the status change, lot creation, and stock movement commit together.
    The QC_PENDING guard makes double-acceptance impossible.
    """
    load = _get_load(db, load_id)
    if load.status != LoadStatus.QC_PENDING:
        raise InvalidStateError(
            f"Load {load.reference} cannot be accepted from status {load.status}"
        )

    weighment = _final_weighment(db, load_id)
    if weighment is None:
        raise InvalidStateError("Load cannot be accepted without a valid weighment")

    if (
        db.execute(select(PaddyLot).where(PaddyLot.load_id == load_id)).scalar_one_or_none()
        is not None
    ):
        raise ConflictError("A paddy lot already exists for this load")

    reference = generate_reference(db, ReferencePrefix.PADDY_LOT)
    paddy_lot = PaddyLot(
        reference=reference,
        load_id=load_id,
        quantity_kg=weighment.net_kg,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(paddy_lot)
    db.flush()

    inventory_service.post_transaction(
        db,
        item_type=InventoryItemType.PADDY_LOT,
        item_id=paddy_lot.id,
        quantity_kg=weighment.net_kg,
        transaction_type=InventoryTransactionType.PADDY_RECEIPT,
        source_type=_LOAD_ENTITY,
        source_id=load.id,
        created_by=actor.user_id,
        notes=f"Paddy receipt from {load.reference}",
    )

    load.status = LoadStatus.ACCEPTED
    load.updated_by = actor.user_id
    record_audit(
        db,
        action="government_load.accept",
        entity_type=_LOAD_ENTITY,
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        before_data={"status": LoadStatus.QC_PENDING},
        after_data={
            "status": load.status,
            "paddy_lot": paddy_lot.reference,
            "quantity_kg": str(paddy_lot.quantity_kg),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(load)
    db.refresh(paddy_lot)
    return load, paddy_lot


def reject_load(
    db: Session, load_id: uuid.UUID, reason: str | None, actor: ActorContext
) -> GovernmentLoad:
    load = _get_load(db, load_id)
    if load.status != LoadStatus.QC_PENDING:
        raise InvalidStateError(
            f"Load {load.reference} cannot be rejected from status {load.status}"
        )
    load.status = LoadStatus.REJECTED
    load.updated_by = actor.user_id
    db.flush()
    record_audit(
        db,
        action="government_load.reject",
        entity_type=_LOAD_ENTITY,
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        before_data={"status": LoadStatus.QC_PENDING},
        after_data={"status": load.status, "reason": reason},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(load)
    return load


# --------------------------------------------------------------------------- #
# Paddy lots / stock
# --------------------------------------------------------------------------- #
def list_paddy_lots(db: Session) -> list[tuple[PaddyLot, Decimal]]:
    lots = list(db.execute(select(PaddyLot).order_by(PaddyLot.reference)).scalars())
    return [
        (
            lot,
            inventory_service.available_quantity(db, InventoryItemType.PADDY_LOT, lot.id),
        )
        for lot in lots
    ]


def get_paddy_lot(db: Session, lot_id: uuid.UUID) -> tuple[PaddyLot, Decimal]:
    lot = db.get(PaddyLot, lot_id)
    if lot is None:
        raise NotFoundError("Paddy lot not found")
    available = inventory_service.available_quantity(db, InventoryItemType.PADDY_LOT, lot.id)
    return lot, available
