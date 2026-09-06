"""Dispatch & delivery tests: rice stock-out (with overspend guard and
exactly-once deduction), the dispatch state machine, and delivery receipts with
shortage/excess calculation.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.inventory.models import InventoryTransaction


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


def _rice_lot(client) -> str:
    """Run receiving + milling + QC to produce a passed rice lot (3000 kg)."""
    agency = client.post("/api/v1/government-agencies", json={"code": "A", "name": "Agency"}).json()
    allocation = client.post(
        "/api/v1/allocations",
        json={"agency_id": agency["id"], "quantity_kg": "20000.000", "allocated_on": "2026-09-01"},
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
        json={"delivery_order_id": order["id"], "lorry_number": "TN01"},
    ).json()
    lid = load["id"]
    client.post(f"/api/v1/government-loads/{lid}/arrive")
    client.post(
        f"/api/v1/government-loads/{lid}/weighments",
        json={"gross_kg": "10000.000", "tare_kg": "2000.000"},
    )
    client.post(
        f"/api/v1/government-loads/{lid}/paddy-quality",
        json={"moisture_pct": "12.00", "foreign_matter_pct": "1.00", "damaged_pct": "1.00"},
    )
    client.post(f"/api/v1/government-loads/{lid}/accept")

    batch = client.post(
        "/api/v1/milling-batches",
        json={
            "inputs": [
                {
                    "paddy_lot_id": client.get("/api/v1/paddy-lots").json()["items"][0]["id"],
                    "quantity_kg": "5000.000",
                }
            ]
        },
    ).json()
    client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    client.post(
        f"/api/v1/milling-batches/{batch['id']}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "3000.000", "bag_weight_kg": "50.000"}
            ]
        },
    )
    client.post(f"/api/v1/milling-batches/{batch['id']}/complete")
    quality_id = client.get("/api/v1/rice-quality?status=PENDING").json()["items"][0]["id"]
    passed = client.post(f"/api/v1/rice-quality/{quality_id}/pass").json()
    return str(passed["rice_lot"]["id"])


def _rice_available(client, lot_id: str) -> Decimal:
    lot = client.get(f"/api/v1/rice-lots/{lot_id}").json()
    return Decimal(str(lot["available_kg"]))


def _dispatch_with_item(client, rice_lot_id: str, qty: str) -> dict[str, object]:
    result: dict[str, object] = client.post(
        "/api/v1/dispatches",
        json={
            "destination_name": "Govt Warehouse #4",
            "lorry_number": "TN22ZZ9",
            "items": [{"rice_lot_id": rice_lot_id, "quantity_kg": qty}],
        },
    ).json()
    return result


# --------------------------------------------------------------------------- #
# Full flow
# --------------------------------------------------------------------------- #
def test_full_dispatch_and_delivery_flow(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    assert _rice_available(client, lot_id) == Decimal("3000.000")

    dispatch = _dispatch_with_item(client, lot_id, "2000.000")
    assert dispatch["reference"] == "DEL-000001"
    assert dispatch["status"] == "DRAFT"

    prepared = client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    assert prepared.json()["status"] == "PREPARED"

    dispatched = client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    assert dispatched.status_code == 200
    assert dispatched.json()["status"] == "DISPATCHED"
    # Rice stock reduced exactly once.
    assert _rice_available(client, lot_id) == Decimal("1000.000")

    receipt = client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "1950.000", "received_bags": 39, "receipt_number": "RCPT-9"},
    )
    assert receipt.status_code == 201
    body = receipt.json()
    assert body["reference"] == "REC-000001"
    assert Decimal(str(body["shortage_kg"])) == Decimal("50.000")
    assert Decimal(str(body["excess_kg"])) == Decimal("0.000")

    assert client.get(f"/api/v1/dispatches/{dispatch['id']}").json()["status"] == "DELIVERED"


def test_delivery_receipt_calculates_excess(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    dispatch = _dispatch_with_item(client, lot_id, "2000.000")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")

    receipt = client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "2100.000"},
    ).json()
    assert Decimal(str(receipt["excess_kg"])) == Decimal("100.000")
    assert Decimal(str(receipt["shortage_kg"])) == Decimal("0.000")


# --------------------------------------------------------------------------- #
# Overspend + exactly-once
# --------------------------------------------------------------------------- #
def test_dispatch_cannot_overspend_rice(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)  # 3000 available
    dispatch = _dispatch_with_item(client, lot_id, "5000.000")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")

    resp = client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "insufficient_stock"
    # Stock untouched; status still PREPARED.
    assert _rice_available(client, lot_id) == Decimal("3000.000")
    assert client.get(f"/api/v1/dispatches/{dispatch['id']}").json()["status"] == "PREPARED"


def test_double_dispatch_prevented(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    dispatch = _dispatch_with_item(client, lot_id, "1000.000")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    assert client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch").status_code == 200
    assert client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch").status_code == 409
    # Deducted once.
    assert _rice_available(client, lot_id) == Decimal("2000.000")


def test_cannot_dispatch_before_prepare(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    dispatch = _dispatch_with_item(client, lot_id, "1000.000")
    resp = client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


# --------------------------------------------------------------------------- #
# Delivery receipt guards
# --------------------------------------------------------------------------- #
def test_receipt_requires_dispatched_and_is_unique(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    dispatch = _dispatch_with_item(client, lot_id, "1000.000")

    # Before dispatch -> 409.
    early = client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "1000.000"},
    )
    assert early.status_code == 409

    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    assert (
        client.post(
            f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
            json={"received_quantity_kg": "1000.000"},
        ).status_code
        == 201
    )
    # Second receipt -> 409 (the dispatch is now DELIVERED, so it is refused).
    dup = client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "1000.000"},
    )
    assert dup.status_code == 409


def test_dispatch_with_unknown_rice_lot_is_404(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    resp = client.post(
        "/api/v1/dispatches",
        json={
            "destination_name": "X",
            "lorry_number": "Y",
            "items": [
                {"rice_lot_id": "00000000-0000-0000-0000-000000000000", "quantity_kg": "1.000"}
            ],
        },
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def test_staff_can_prepare_but_not_dispatch(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)

    client.cookies.clear()
    _login(client, "staff", "staff-passphrase-1")
    dispatch = _dispatch_with_item(client, lot_id, "1000.000")
    assert client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare").status_code == 200
    # Staff lacks dispatch.confirm.
    assert client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch").status_code == 403


def test_dispatch_audit_trail(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _rice_lot(client)
    dispatch = _dispatch_with_item(client, lot_id, "1000.000")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "1000.000"},
    )

    with SessionLocal() as db:
        # Exactly one rice dispatch movement was posted.
        moves = [
            t
            for t in db.execute(select(InventoryTransaction)).scalars().all()
            if t.transaction_type == "RICE_DISPATCH"
        ]
        assert len(moves) == 1
        assert Decimal(moves[0].quantity_kg) == Decimal("-1000.000")
