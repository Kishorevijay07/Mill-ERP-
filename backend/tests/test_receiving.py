"""Receiving flow tests: weighment, paddy QC, accept/reject, paddy lot + stock.

Exercises the load state machine (ARRIVED -> WEIGHED -> QC_PENDING ->
ACCEPTED/REJECTED), the net-weight calculation, RBAC, and that acceptance is the
only way paddy stock is created (via an inventory transaction).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import (
    InventoryItemType,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.shared.audit import AuditLog


def _login(client, identifier: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": password},
    )


def _users(make_user) -> None:
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


def _make_arrived_load(client) -> str:
    """As the logged-in user, build agency -> allocation -> DO -> load, then arrive."""
    agency = client.post("/api/v1/government-agencies", json={"code": "A", "name": "Agency"}).json()
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
            "do_number": "D1",
            "quantity_kg": "10000.000",
            "issued_on": "2026-09-02",
        },
    ).json()
    load = client.post(
        "/api/v1/government-loads",
        json={"delivery_order_id": order["id"], "lorry_number": "TN01AB1234"},
    ).json()
    client.post(f"/api/v1/government-loads/{load['id']}/arrive")
    return str(load["id"])


def _record_weighment(client, load_id: str, gross: str = "10000.000", tare: str = "2000.000"):
    return client.post(
        f"/api/v1/government-loads/{load_id}/weighments",
        json={"gross_kg": gross, "tare_kg": tare},
    )


def _record_quality(client, load_id: str):
    return client.post(
        f"/api/v1/government-loads/{load_id}/paddy-quality",
        json={"moisture_pct": "12.50", "foreign_matter_pct": "1.20", "damaged_pct": "2.00"},
    )


# --------------------------------------------------------------------------- #
# Weighment
# --------------------------------------------------------------------------- #
def test_weighment_computes_net_and_transitions_to_weighed(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)

    resp = _record_weighment(client, load_id, "10000.000", "2000.000")
    assert resp.status_code == 201
    assert Decimal(str(resp.json()["net_kg"])) == Decimal("8000.000")
    assert resp.json()["is_final"] is True

    load = client.get(f"/api/v1/government-loads/{load_id}").json()
    assert load["status"] == "WEIGHED"


def test_weighment_requires_arrived_state(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    # Create a load but do NOT arrive it (status DRAFT).
    agency = client.post("/api/v1/government-agencies", json={"code": "A", "name": "A"}).json()
    allocation = client.post(
        "/api/v1/allocations",
        json={"agency_id": agency["id"], "quantity_kg": "1.000", "allocated_on": "2026-09-01"},
    ).json()
    order = client.post(
        "/api/v1/delivery-orders",
        json={
            "allocation_id": allocation["id"],
            "do_number": "D",
            "quantity_kg": "1.000",
            "issued_on": "2026-09-02",
        },
    ).json()
    load = client.post(
        "/api/v1/government-loads",
        json={"delivery_order_id": order["id"], "lorry_number": "T"},
    ).json()

    resp = _record_weighment(client, load["id"])
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_weighment_gross_must_exceed_tare(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)

    resp = _record_weighment(client, load_id, gross="100.000", tare="200.000")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_weighment_negative_tare_rejected_by_validation(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)

    resp = client.post(
        f"/api/v1/government-loads/{load_id}/weighments",
        json={"gross_kg": "100.000", "tare_kg": "-1.000"},
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Paddy quality
# --------------------------------------------------------------------------- #
def test_quality_transitions_to_qc_pending(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)

    resp = _record_quality(client, load_id)
    assert resp.status_code == 201
    load = client.get(f"/api/v1/government-loads/{load_id}").json()
    assert load["status"] == "QC_PENDING"


def test_quality_percentage_out_of_range_rejected(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)

    resp = client.post(
        f"/api/v1/government-loads/{load_id}/paddy-quality",
        json={"moisture_pct": "150.00", "foreign_matter_pct": "1.00", "damaged_pct": "1.00"},
    )
    assert resp.status_code == 422


# --------------------------------------------------------------------------- #
# Accept / reject
# --------------------------------------------------------------------------- #
def test_full_accept_flow_creates_lot_and_stock(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id, "10000.000", "2000.000")
    _record_quality(client, load_id)

    accepted = client.post(f"/api/v1/government-loads/{load_id}/accept")
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["load"]["status"] == "ACCEPTED"
    assert body["paddy_lot"]["reference"] == "PL-000001"
    assert Decimal(str(body["paddy_lot"]["quantity_kg"])) == Decimal("8000.000")

    # Stock is available via inventory.
    lot = client.get(f"/api/v1/paddy-lots/{body['paddy_lot']['id']}").json()
    assert Decimal(str(lot["available_kg"])) == Decimal("8000.000")

    # Exactly one positive inventory movement was posted.
    with SessionLocal() as db:
        txns = db.execute(select(InventoryTransaction)).scalars().all()
        assert len(txns) == 1
        assert txns[0].transaction_type == "PADDY_RECEIPT"
        assert Decimal(txns[0].quantity_kg) == Decimal("8000.000")


def test_accept_requires_qc_pending(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)
    # No QC recorded yet -> still WEIGHED.
    resp = client.post(f"/api/v1/government-loads/{load_id}/accept")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_double_accept_is_prevented(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)
    _record_quality(client, load_id)
    assert client.post(f"/api/v1/government-loads/{load_id}/accept").status_code == 200

    second = client.post(f"/api/v1/government-loads/{load_id}/accept")
    assert second.status_code == 409

    # Still exactly one stock movement — no duplicate deduction/receipt.
    with SessionLocal() as db:
        assert len(db.execute(select(InventoryTransaction)).scalars().all()) == 1


def test_reject_flow(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)
    _record_quality(client, load_id)

    rejected = client.post(
        f"/api/v1/government-loads/{load_id}/reject", json={"reason": "High moisture"}
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"

    # A rejected load cannot be accepted, and no stock exists.
    assert client.post(f"/api/v1/government-loads/{load_id}/accept").status_code == 409
    with SessionLocal() as db:
        assert db.execute(select(InventoryTransaction)).scalars().first() is None


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def test_staff_can_weigh_and_qc_but_not_accept(client, make_user) -> None:
    _users(make_user)
    # Owner sets up and arrives the load.
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)

    # Staff records weighment and QC (has receiving permissions).
    client.cookies.clear()
    _login(client, "staff", "staff-passphrase-1")
    assert _record_weighment(client, load_id).status_code == 201
    assert _record_quality(client, load_id).status_code == 201

    # Staff cannot accept.
    assert client.post(f"/api/v1/government-loads/{load_id}/accept").status_code == 403


# --------------------------------------------------------------------------- #
# Inventory guard (unit)
# --------------------------------------------------------------------------- #
def test_inventory_rejects_overspend(db_session) -> None:
    import uuid

    item = uuid.uuid4()
    inventory_service.post_transaction(
        db_session,
        item_type=InventoryItemType.PADDY_LOT,
        item_id=item,
        quantity_kg=Decimal("100.000"),
        transaction_type=InventoryTransactionType.PADDY_RECEIPT,
        source_type="test",
    )
    db_session.commit()
    assert inventory_service.available_quantity(
        db_session, InventoryItemType.PADDY_LOT, item
    ) == Decimal("100.000")

    with pytest.raises(inventory_service.InsufficientStockError):
        inventory_service.post_transaction(
            db_session,
            item_type=InventoryItemType.PADDY_LOT,
            item_id=item,
            quantity_kg=Decimal("-150.000"),
            transaction_type=InventoryTransactionType.PADDY_CONSUMPTION,
            source_type="test",
        )


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
def test_receiving_actions_are_audited(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    load_id = _make_arrived_load(client)
    _record_weighment(client, load_id)
    _record_quality(client, load_id)
    client.post(f"/api/v1/government-loads/{load_id}/accept")

    with SessionLocal() as db:
        actions = set(db.execute(select(AuditLog.action)).scalars().all())
    assert {
        "weighment.record",
        "paddy_quality.record",
        "government_load.accept",
    }.issubset(actions)
