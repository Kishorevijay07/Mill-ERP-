"""Government receiving domain logic.

Each mutation runs in a single transaction that: allocates a business reference
(where applicable), writes the record with the acting user stamped, appends an
audit entry, and commits atomically. Parent references are validated so the
domain chain (agency -> allocation -> delivery order -> load) stays intact.
"""

from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.government.models import (
    Allocation,
    DeliveryOrder,
    GovernmentAgency,
    GovernmentLoad,
    LoadStatus,
)
from app.modules.government.schemas import (
    AgencyCreate,
    AllocationCreate,
    DeliveryOrderCreate,
    LoadCreate,
)
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

T = TypeVar("T")


def _paginate(
    db: Session, stmt: Select[tuple[T]], page: int, page_size: int
) -> tuple[list[T], int]:
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = list(db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all())
    return rows, total


# --------------------------------------------------------------------------- #
# Agencies
# --------------------------------------------------------------------------- #
def create_agency(db: Session, data: AgencyCreate, actor: ActorContext) -> GovernmentAgency:
    existing = db.execute(
        select(GovernmentAgency).where(GovernmentAgency.code == data.code)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"Agency code '{data.code}' already exists")

    agency = GovernmentAgency(
        code=data.code,
        name=data.name,
        contact_name=data.contact_name,
        contact_phone=data.contact_phone,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(agency)
    db.flush()
    record_audit(
        db,
        action="government_agency.create",
        entity_type="government_agency",
        entity_id=agency.id,
        entity_reference=agency.code,
        user_id=actor.user_id,
        after_data={"code": agency.code, "name": agency.name},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(agency)
    return agency


def list_agencies(db: Session, page: int, page_size: int) -> tuple[list[GovernmentAgency], int]:
    stmt = select(GovernmentAgency).order_by(GovernmentAgency.code)
    return _paginate(db, stmt, page, page_size)


def get_agency(db: Session, agency_id: uuid.UUID) -> GovernmentAgency:
    agency = db.get(GovernmentAgency, agency_id)
    if agency is None:
        raise NotFoundError("Agency not found")
    return agency


# --------------------------------------------------------------------------- #
# Allocations
# --------------------------------------------------------------------------- #
def create_allocation(db: Session, data: AllocationCreate, actor: ActorContext) -> Allocation:
    if db.get(GovernmentAgency, data.agency_id) is None:
        raise NotFoundError("Agency not found")

    reference = generate_reference(db, ReferencePrefix.ALLOCATION)
    allocation = Allocation(
        reference=reference,
        agency_id=data.agency_id,
        quantity_kg=data.quantity_kg,
        allocated_on=data.allocated_on,
        season=data.season,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(allocation)
    db.flush()
    record_audit(
        db,
        action="allocation.create",
        entity_type="allocation",
        entity_id=allocation.id,
        entity_reference=allocation.reference,
        user_id=actor.user_id,
        after_data={
            "agency_id": str(allocation.agency_id),
            "quantity_kg": str(allocation.quantity_kg),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(allocation)
    return allocation


def list_allocations(db: Session, page: int, page_size: int) -> tuple[list[Allocation], int]:
    stmt = select(Allocation).order_by(Allocation.reference)
    return _paginate(db, stmt, page, page_size)


def get_allocation(db: Session, allocation_id: uuid.UUID) -> Allocation:
    allocation = db.get(Allocation, allocation_id)
    if allocation is None:
        raise NotFoundError("Allocation not found")
    return allocation


# --------------------------------------------------------------------------- #
# Delivery orders
# --------------------------------------------------------------------------- #
def create_delivery_order(
    db: Session, data: DeliveryOrderCreate, actor: ActorContext
) -> DeliveryOrder:
    if db.get(Allocation, data.allocation_id) is None:
        raise NotFoundError("Allocation not found")

    reference = generate_reference(db, ReferencePrefix.DELIVERY_ORDER)
    order = DeliveryOrder(
        reference=reference,
        allocation_id=data.allocation_id,
        do_number=data.do_number,
        quantity_kg=data.quantity_kg,
        issued_on=data.issued_on,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(order)
    db.flush()
    record_audit(
        db,
        action="delivery_order.create",
        entity_type="delivery_order",
        entity_id=order.id,
        entity_reference=order.reference,
        user_id=actor.user_id,
        after_data={
            "allocation_id": str(order.allocation_id),
            "do_number": order.do_number,
            "quantity_kg": str(order.quantity_kg),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(order)
    return order


def list_delivery_orders(db: Session, page: int, page_size: int) -> tuple[list[DeliveryOrder], int]:
    stmt = select(DeliveryOrder).order_by(DeliveryOrder.reference)
    return _paginate(db, stmt, page, page_size)


def get_delivery_order(db: Session, order_id: uuid.UUID) -> DeliveryOrder:
    order = db.get(DeliveryOrder, order_id)
    if order is None:
        raise NotFoundError("Delivery order not found")
    return order


# --------------------------------------------------------------------------- #
# Government loads
# --------------------------------------------------------------------------- #
def create_load(db: Session, data: LoadCreate, actor: ActorContext) -> GovernmentLoad:
    if db.get(DeliveryOrder, data.delivery_order_id) is None:
        raise NotFoundError("Delivery order not found")

    reference = generate_reference(db, ReferencePrefix.LOAD)
    load = GovernmentLoad(
        reference=reference,
        delivery_order_id=data.delivery_order_id,
        lorry_number=data.lorry_number,
        driver_name=data.driver_name,
        declared_quantity_kg=data.declared_quantity_kg,
        status=LoadStatus.DRAFT,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(load)
    db.flush()
    record_audit(
        db,
        action="government_load.create",
        entity_type="government_load",
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        after_data={"status": load.status, "lorry_number": load.lorry_number},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(load)
    return load


def list_loads(db: Session, page: int, page_size: int) -> tuple[list[GovernmentLoad], int]:
    stmt = select(GovernmentLoad).order_by(GovernmentLoad.reference)
    return _paginate(db, stmt, page, page_size)


def get_load(db: Session, load_id: uuid.UUID) -> GovernmentLoad:
    load = db.get(GovernmentLoad, load_id)
    if load is None:
        raise NotFoundError("Government load not found")
    return load


def mark_load_arrived(db: Session, load_id: uuid.UUID, actor: ActorContext) -> GovernmentLoad:
    """Transition DRAFT -> ARRIVED.

    Later transitions (WEIGHED, QC_PENDING, ACCEPTED/REJECTED) are added with the
    weighment and quality modules; they must not be reachable via a generic PATCH.
    """
    load = get_load(db, load_id)
    if load.status != LoadStatus.DRAFT:
        raise InvalidStateError(f"Load {load.reference} cannot arrive from status {load.status}")
    before = load.status
    load.status = LoadStatus.ARRIVED
    load.updated_by = actor.user_id
    record_audit(
        db,
        action="government_load.arrive",
        entity_type="government_load",
        entity_id=load.id,
        entity_reference=load.reference,
        user_id=actor.user_id,
        before_data={"status": before},
        after_data={"status": load.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(load)
    return load
