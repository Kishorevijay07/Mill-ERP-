"""Government receiving HTTP endpoints.

Thin layer: resolve the actor, enforce the permission (server-side), delegate to
the service, shape the response. State transitions are explicit action endpoints,
never a generic status PATCH (docs/API-SPEC.md).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.government import service
from app.modules.government.schemas import (
    AgencyCreate,
    AgencyOut,
    AllocationCreate,
    AllocationOut,
    DeliveryOrderCreate,
    DeliveryOrderOut,
    LoadCreate,
    LoadOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["government"])


# --------------------------------------------------------------------------- #
# Agencies
# --------------------------------------------------------------------------- #
@router.post(
    "/government-agencies",
    response_model=AgencyOut,
    status_code=status.HTTP_201_CREATED,
)
def create_agency(
    payload: AgencyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_AGENCY_MANAGE)),
) -> AgencyOut:
    agency = service.create_agency(db, payload, _actor(request, user))
    return AgencyOut.model_validate(agency)


@router.get("/government-agencies", response_model=Page[AgencyOut])
def list_agencies(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_AGENCY_VIEW)),
) -> Page[AgencyOut]:
    rows, total = service.list_agencies(db, pagination.page, pagination.page_size)
    return Page[AgencyOut](
        items=[AgencyOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/government-agencies/{agency_id}", response_model=AgencyOut)
def get_agency(
    agency_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_AGENCY_VIEW)),
) -> AgencyOut:
    return AgencyOut.model_validate(service.get_agency(db, agency_id))


# --------------------------------------------------------------------------- #
# Allocations
# --------------------------------------------------------------------------- #
@router.post(
    "/allocations",
    response_model=AllocationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_allocation(
    payload: AllocationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_ALLOCATION_MANAGE)),
) -> AllocationOut:
    allocation = service.create_allocation(db, payload, _actor(request, user))
    return AllocationOut.model_validate(allocation)


@router.get("/allocations", response_model=Page[AllocationOut])
def list_allocations(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_ALLOCATION_VIEW)),
) -> Page[AllocationOut]:
    rows, total = service.list_allocations(db, pagination.page, pagination.page_size)
    return Page[AllocationOut](
        items=[AllocationOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/allocations/{allocation_id}", response_model=AllocationOut)
def get_allocation(
    allocation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_ALLOCATION_VIEW)),
) -> AllocationOut:
    return AllocationOut.model_validate(service.get_allocation(db, allocation_id))


# --------------------------------------------------------------------------- #
# Delivery orders
# --------------------------------------------------------------------------- #
@router.post(
    "/delivery-orders",
    response_model=DeliveryOrderOut,
    status_code=status.HTTP_201_CREATED,
)
def create_delivery_order(
    payload: DeliveryOrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_DELIVERY_ORDER_MANAGE)),
) -> DeliveryOrderOut:
    order = service.create_delivery_order(db, payload, _actor(request, user))
    return DeliveryOrderOut.model_validate(order)


@router.get("/delivery-orders", response_model=Page[DeliveryOrderOut])
def list_delivery_orders(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_DELIVERY_ORDER_VIEW)),
) -> Page[DeliveryOrderOut]:
    rows, total = service.list_delivery_orders(db, pagination.page, pagination.page_size)
    return Page[DeliveryOrderOut](
        items=[DeliveryOrderOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/delivery-orders/{order_id}", response_model=DeliveryOrderOut)
def get_delivery_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_DELIVERY_ORDER_VIEW)),
) -> DeliveryOrderOut:
    return DeliveryOrderOut.model_validate(service.get_delivery_order(db, order_id))


# --------------------------------------------------------------------------- #
# Government loads
# --------------------------------------------------------------------------- #
@router.post(
    "/government-loads",
    response_model=LoadOut,
    status_code=status.HTTP_201_CREATED,
)
def create_load(
    payload: LoadCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_CREATE)),
) -> LoadOut:
    load = service.create_load(db, payload, _actor(request, user))
    return LoadOut.model_validate(load)


@router.get("/government-loads", response_model=Page[LoadOut])
def list_loads(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_VIEW)),
) -> Page[LoadOut]:
    rows, total = service.list_loads(db, pagination.page, pagination.page_size)
    return Page[LoadOut](
        items=[LoadOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/government-loads/{load_id}", response_model=LoadOut)
def get_load(
    load_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_VIEW)),
) -> LoadOut:
    return LoadOut.model_validate(service.get_load(db, load_id))


@router.post("/government-loads/{load_id}/arrive", response_model=LoadOut)
def arrive_load(
    load_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.GOVERNMENT_LOAD_CREATE)),
) -> LoadOut:
    load = service.mark_load_arrived(db, load_id, _actor(request, user))
    return LoadOut.model_validate(load)
