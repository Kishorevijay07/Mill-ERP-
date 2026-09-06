"""Government receiving API tests: the agency -> allocation -> DO -> load chain,
reference numbering, RBAC enforcement, the DRAFT -> ARRIVED transition, and audit.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.shared.audit import AuditLog


def _login(client, identifier: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )


def _make_owner_and_staff(make_user) -> None:
    make_user(
        email="owner@example.com",
        username="owner",
        password="owner-passphrase-1",
        role_codes=("OWNER",),
    )
    make_user(
        email="staff@example.com",
        username="staff",
        password="staff-passphrase-1",
        role_codes=("STAFF",),
    )


def _create_chain(client) -> dict[str, dict[str, object]]:
    """Create agency -> allocation -> DO -> load as the logged-in owner."""
    agency = client.post(
        "/api/v1/government-agencies",
        json={"code": "TNCSC", "name": "TN Civil Supplies"},
    ).json()
    allocation = client.post(
        "/api/v1/allocations",
        json={
            "agency_id": agency["id"],
            "quantity_kg": "20000.000",
            "allocated_on": "2026-09-01",
        },
    ).json()
    order = client.post(
        "/api/v1/delivery-orders",
        json={
            "allocation_id": allocation["id"],
            "do_number": "DO-GOVT-42",
            "quantity_kg": "10000.000",
            "issued_on": "2026-09-02",
        },
    ).json()
    load = client.post(
        "/api/v1/government-loads",
        json={
            "delivery_order_id": order["id"],
            "lorry_number": "TN01AB1234",
            "declared_quantity_kg": "9800.500",
        },
    ).json()
    return {"agency": agency, "allocation": allocation, "order": order, "load": load}


# --------------------------------------------------------------------------- #
# Happy path: full chain, reference numbering
# --------------------------------------------------------------------------- #
def test_owner_can_create_full_chain_with_references(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")

    chain = _create_chain(client)
    assert chain["allocation"]["reference"] == "AL-000001"
    assert chain["order"]["reference"] == "DO-000001"
    assert chain["load"]["reference"] == "LD-000001"
    assert chain["load"]["status"] == "DRAFT"


def test_references_increment_per_prefix(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    first = _create_chain(client)

    second_alloc = client.post(
        "/api/v1/allocations",
        json={
            "agency_id": first["agency"]["id"],
            "quantity_kg": "5000.000",
            "allocated_on": "2026-09-03",
        },
    ).json()
    assert second_alloc["reference"] == "AL-000002"


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def test_staff_cannot_create_agency_but_can_view(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "staff", "staff-passphrase-1")

    created = client.post(
        "/api/v1/government-agencies",
        json={"code": "X", "name": "X"},
    )
    assert created.status_code == 403

    listed = client.get("/api/v1/government-agencies")
    assert listed.status_code == 200


def test_staff_can_create_load(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    # Owner sets up the chain up to the delivery order.
    _login(client, "owner", "owner-passphrase-1")
    agency = client.post("/api/v1/government-agencies", json={"code": "A", "name": "A"}).json()
    allocation = client.post(
        "/api/v1/allocations",
        json={
            "agency_id": agency["id"],
            "quantity_kg": "1000.000",
            "allocated_on": "2026-09-01",
        },
    ).json()
    order = client.post(
        "/api/v1/delivery-orders",
        json={
            "allocation_id": allocation["id"],
            "do_number": "D1",
            "quantity_kg": "500.000",
            "issued_on": "2026-09-02",
        },
    ).json()

    # Staff (GOVERNMENT_LOAD_CREATE) creates the load.
    client.cookies.clear()
    _login(client, "staff", "staff-passphrase-1")
    load = client.post(
        "/api/v1/government-loads",
        json={"delivery_order_id": order["id"], "lorry_number": "TN01"},
    )
    assert load.status_code == 201


def test_endpoints_require_authentication(client) -> None:
    assert client.get("/api/v1/government-loads").status_code == 401
    assert (
        client.post("/api/v1/government-agencies", json={"code": "A", "name": "A"}).status_code
        == 401
    )


# --------------------------------------------------------------------------- #
# Validation / not found
# --------------------------------------------------------------------------- #
def test_allocation_with_unknown_agency_is_404(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    resp = client.post(
        "/api/v1/allocations",
        json={
            "agency_id": "00000000-0000-0000-0000-000000000000",
            "quantity_kg": "10.000",
            "allocated_on": "2026-09-01",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_duplicate_agency_code_is_409(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    client.post("/api/v1/government-agencies", json={"code": "DUP", "name": "One"})
    resp = client.post("/api/v1/government-agencies", json={"code": "DUP", "name": "Two"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_negative_quantity_rejected_by_validation(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    agency = client.post("/api/v1/government-agencies", json={"code": "A", "name": "A"}).json()
    resp = client.post(
        "/api/v1/allocations",
        json={
            "agency_id": agency["id"],
            "quantity_kg": "-5.000",
            "allocated_on": "2026-09-01",
        },
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# State machine: DRAFT -> ARRIVED
# --------------------------------------------------------------------------- #
def test_load_arrive_transition_and_guard(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    chain = _create_chain(client)
    load_id = chain["load"]["id"]

    arrived = client.post(f"/api/v1/government-loads/{load_id}/arrive")
    assert arrived.status_code == 200
    assert arrived.json()["status"] == "ARRIVED"

    # Arriving again is an invalid transition.
    again = client.post(f"/api/v1/government-loads/{load_id}/arrive")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "invalid_state"


# --------------------------------------------------------------------------- #
# Audit trail
# --------------------------------------------------------------------------- #
def test_mutations_are_audited(client, make_user) -> None:
    _make_owner_and_staff(make_user)
    _login(client, "owner", "owner-passphrase-1")
    chain = _create_chain(client)
    client.post(f"/api/v1/government-loads/{chain['load']['id']}/arrive")

    with SessionLocal() as db:
        actions = set(db.execute(select(AuditLog.action)).scalars().all())

    assert {
        "government_agency.create",
        "allocation.create",
        "delivery_order.create",
        "government_load.create",
        "government_load.arrive",
    }.issubset(actions)
