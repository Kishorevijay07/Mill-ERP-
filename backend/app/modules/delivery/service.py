"""Dispatch & delivery domain logic.

- Dispatching (PREPARED -> DISPATCHED) deducts rice stock: each item's rice lot
  is locked, its balance checked, and a negative movement posted. A dispatch that
  would exceed available stock is refused; the status guard makes the stock-out
  happen exactly once.
- A delivery receipt (1:1 with the dispatch) records the received quantity and
  computes shortage/excess, then marks the dispatch DELIVERED.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.delivery.models import (
    DeliveryReceipt,
    Dispatch,
    DispatchItem,
    DispatchStatus,
)
from app.modules.delivery.schemas import DeliveryReceiptCreate, DispatchCreate
from app.modules.government.models import DeliveryOrder, GovernmentAgency
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import InventoryItemType, InventoryTransactionType
from app.modules.rice.models import RiceLot
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

_DISPATCH_ENTITY = "dispatch"


def _now() -> datetime:
    return datetime.now(UTC)


def _get_dispatch(db: Session, dispatch_id: uuid.UUID) -> Dispatch:
    dispatch = db.get(Dispatch, dispatch_id)
    if dispatch is None:
        raise NotFoundError("Dispatch not found")
    return dispatch


def _load_dispatch(db: Session, dispatch_id: uuid.UUID) -> Dispatch:
    dispatch = db.execute(
        select(Dispatch)
        .options(selectinload(Dispatch.items), selectinload(Dispatch.receipt))
        .where(Dispatch.id == dispatch_id)
    ).scalar_one_or_none()
    if dispatch is None:
        raise NotFoundError("Dispatch not found")
    return dispatch


def create_dispatch(db: Session, data: DispatchCreate, actor: ActorContext) -> Dispatch:
    # Aggregate the requested quantity per rice lot and validate it against the
    # available balance up front, so an operator cannot build (and later prepare)
    # a dispatch that can never be fulfilled. The row-locked check at dispatch
    # time remains the final authority against concurrent stock-outs.
    requested_by_lot: dict[uuid.UUID, Decimal] = {}
    for item in data.items:
        requested_by_lot[item.rice_lot_id] = (
            requested_by_lot.get(item.rice_lot_id, Decimal("0")) + item.quantity_kg
        )
    for rice_lot_id, requested in requested_by_lot.items():
        lot = db.get(RiceLot, rice_lot_id)
        if lot is None:
            raise NotFoundError(f"Rice lot {rice_lot_id} not found")
        available = inventory_service.available_quantity(
            db, InventoryItemType.RICE_LOT, rice_lot_id
        )
        if requested > available:
            raise inventory_service.InsufficientStockError(
                f"Insufficient stock for rice lot {lot.reference}: "
                f"available {available}, requested {requested}"
            )
    if (
        data.destination_agency_id is not None
        and db.get(GovernmentAgency, data.destination_agency_id) is None
    ):
        raise NotFoundError("Destination agency not found")
    if data.delivery_order_id is not None and db.get(DeliveryOrder, data.delivery_order_id) is None:
        raise NotFoundError("Delivery order not found")

    reference = generate_reference(db, ReferencePrefix.DISPATCH)
    dispatch = Dispatch(
        reference=reference,
        status=DispatchStatus.DRAFT,
        destination_name=data.destination_name,
        destination_agency_id=data.destination_agency_id,
        delivery_order_id=data.delivery_order_id,
        lorry_number=data.lorry_number,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(dispatch)
    db.flush()
    for item in data.items:
        db.add(
            DispatchItem(
                dispatch_id=dispatch.id,
                rice_lot_id=item.rice_lot_id,
                quantity_kg=item.quantity_kg,
                created_by=actor.user_id,
                updated_by=actor.user_id,
            )
        )
    record_audit(
        db,
        action="dispatch.create",
        entity_type=_DISPATCH_ENTITY,
        entity_id=dispatch.id,
        entity_reference=dispatch.reference,
        user_id=actor.user_id,
        after_data={"status": dispatch.status, "items": len(data.items)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _load_dispatch(db, dispatch.id)


def list_dispatches(db: Session, page: int, page_size: int) -> tuple[list[Dispatch], int]:
    total = db.execute(select(func.count()).select_from(Dispatch)).scalar_one()
    rows = list(
        db.execute(
            select(Dispatch)
            .order_by(Dispatch.reference)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()
    )
    return rows, total


def get_dispatch(db: Session, dispatch_id: uuid.UUID) -> Dispatch:
    return _load_dispatch(db, dispatch_id)


def _dispatch_items(db: Session, dispatch_id: uuid.UUID) -> list[DispatchItem]:
    return list(
        db.execute(select(DispatchItem).where(DispatchItem.dispatch_id == dispatch_id)).scalars()
    )


def prepare_dispatch(db: Session, dispatch_id: uuid.UUID, actor: ActorContext) -> Dispatch:
    dispatch = _get_dispatch(db, dispatch_id)
    if dispatch.status != DispatchStatus.DRAFT:
        raise InvalidStateError(
            f"Dispatch {dispatch.reference} cannot be prepared from status {dispatch.status}"
        )
    if not _dispatch_items(db, dispatch_id):
        raise InvalidStateError("Dispatch has no items")
    dispatch.status = DispatchStatus.PREPARED
    dispatch.updated_by = actor.user_id
    record_audit(
        db,
        action="dispatch.prepare",
        entity_type=_DISPATCH_ENTITY,
        entity_id=dispatch.id,
        entity_reference=dispatch.reference,
        user_id=actor.user_id,
        after_data={"status": dispatch.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _load_dispatch(db, dispatch_id)


def dispatch_dispatch(db: Session, dispatch_id: uuid.UUID, actor: ActorContext) -> Dispatch:
    """PREPARED -> DISPATCHED, deducting rice stock for each item under a lock."""
    dispatch = _get_dispatch(db, dispatch_id)
    if dispatch.status != DispatchStatus.PREPARED:
        raise InvalidStateError(
            f"Dispatch {dispatch.reference} cannot dispatch from status {dispatch.status}"
        )

    for item in _dispatch_items(db, dispatch_id):
        # Lock the rice lot so concurrent dispatches cannot overspend it.
        db.get(RiceLot, item.rice_lot_id, with_for_update=True)
        inventory_service.post_transaction(
            db,
            item_type=InventoryItemType.RICE_LOT,
            item_id=item.rice_lot_id,
            quantity_kg=-item.quantity_kg,
            transaction_type=InventoryTransactionType.RICE_DISPATCH,
            source_type=_DISPATCH_ENTITY,
            source_id=dispatch.id,
            created_by=actor.user_id,
            notes=f"Dispatched on {dispatch.reference}",
        )

    dispatch.status = DispatchStatus.DISPATCHED
    dispatch.dispatched_at = _now()
    dispatch.updated_by = actor.user_id
    record_audit(
        db,
        action="dispatch.dispatch",
        entity_type=_DISPATCH_ENTITY,
        entity_id=dispatch.id,
        entity_reference=dispatch.reference,
        user_id=actor.user_id,
        before_data={"status": DispatchStatus.PREPARED},
        after_data={"status": dispatch.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _load_dispatch(db, dispatch_id)


def create_delivery_receipt(
    db: Session, dispatch_id: uuid.UUID, data: DeliveryReceiptCreate, actor: ActorContext
) -> DeliveryReceipt:
    dispatch = _get_dispatch(db, dispatch_id)
    if dispatch.status != DispatchStatus.DISPATCHED:
        raise InvalidStateError(
            f"Dispatch {dispatch.reference} must be DISPATCHED to record a receipt"
        )
    if (
        db.execute(
            select(DeliveryReceipt).where(DeliveryReceipt.dispatch_id == dispatch_id)
        ).scalar_one_or_none()
        is not None
    ):
        raise ConflictError("A delivery receipt already exists for this dispatch")

    dispatched_qty = sum(
        (item.quantity_kg for item in _dispatch_items(db, dispatch_id)), Decimal("0")
    )
    received = data.received_quantity_kg
    shortage = dispatched_qty - received if dispatched_qty > received else Decimal("0")
    excess = received - dispatched_qty if received > dispatched_qty else Decimal("0")

    reference = generate_reference(db, ReferencePrefix.DELIVERY_RECEIPT)
    receipt = DeliveryReceipt(
        reference=reference,
        dispatch_id=dispatch_id,
        dispatched_quantity_kg=dispatched_qty,
        received_quantity_kg=received,
        received_bags=data.received_bags,
        shortage_kg=shortage,
        excess_kg=excess,
        receipt_number=data.receipt_number,
        receipt_date=data.receipt_date,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(receipt)
    dispatch.status = DispatchStatus.DELIVERED
    dispatch.updated_by = actor.user_id
    db.flush()
    record_audit(
        db,
        action="delivery_receipt.create",
        entity_type="delivery_receipt",
        entity_id=receipt.id,
        entity_reference=receipt.reference,
        user_id=actor.user_id,
        after_data={
            "dispatch": dispatch.reference,
            "received_kg": str(received),
            "shortage_kg": str(shortage),
            "excess_kg": str(excess),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(receipt)
    return receipt


def list_receipts(db: Session, page: int, page_size: int) -> tuple[list[DeliveryReceipt], int]:
    total = db.execute(select(func.count()).select_from(DeliveryReceipt)).scalar_one()
    rows = list(
        db.execute(
            select(DeliveryReceipt)
            .order_by(DeliveryReceipt.reference)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()
    )
    return rows, total


def get_receipt(db: Session, receipt_id: uuid.UUID) -> DeliveryReceipt:
    receipt = db.get(DeliveryReceipt, receipt_id)
    if receipt is None:
        raise NotFoundError("Delivery receipt not found")
    return receipt
