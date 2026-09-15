"""Milling & rice tests: paddy consumption (with overspend guard), rice
production, bag-count calculation, QC pass/fail, rice-lot + stock creation, and
the batch/QC state machines.
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


def _accepted_paddy_lot(client) -> str:
    """Run the receiving flow (as the logged-in owner) and return the paddy lot id.

    Produces a lot with 8000.000 kg available (gross 10000 - tare 2000).
    """
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
    client.post(f"/api/v1/government-loads/{load['id']}/arrive")
    client.post(
        f"/api/v1/government-loads/{load['id']}/weighments",
        json={"gross_kg": "10000.000", "tare_kg": "2000.000"},
    )
    client.post(
        f"/api/v1/government-loads/{load['id']}/paddy-quality",
        json={"moisture_pct": "12.00", "foreign_matter_pct": "1.00", "damaged_pct": "1.00"},
    )
    accepted = client.post(f"/api/v1/government-loads/{load['id']}/accept").json()
    return str(accepted["paddy_lot"]["id"])


def _available(client, lot_id: str) -> Decimal:
    lot = client.get(f"/api/v1/paddy-lots/{lot_id}").json()
    return Decimal(str(lot["available_kg"]))


# --------------------------------------------------------------------------- #
# Happy path: batch -> consume -> produce -> complete -> QC -> rice lot
# --------------------------------------------------------------------------- #
def test_full_milling_and_rice_flow(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    assert _available(client, lot_id) == Decimal("8000.000")

    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "5000.000"}]},
    ).json()
    assert batch["reference"] == "MB-000001"
    assert batch["status"] == "DRAFT"

    started = client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    assert started.status_code == 200
    assert started.json()["status"] == "IN_PROGRESS"
    # Paddy consumed exactly once.
    assert _available(client, lot_id) == Decimal("3000.000")

    production = client.post(
        f"/api/v1/milling-batches/{batch['id']}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "3000.000", "bag_weight_kg": "50.000"},
                {"category": "CATEGORY_2", "quantity_kg": "1500.000", "bag_weight_kg": "25.000"},
            ]
        },
    )
    assert production.status_code == 201
    outputs = production.json()["outputs"]
    assert outputs[0]["bag_count"] == 60  # 3000 / 50
    assert outputs[1]["bag_count"] == 60  # 1500 / 25

    completed = client.post(f"/api/v1/milling-batches/{batch['id']}/complete")
    assert completed.json()["status"] == "COMPLETED"

    # Two PENDING QC records now exist.
    pending = client.get("/api/v1/rice-quality?status=PENDING").json()
    assert pending["total"] == 2

    # Pass the first, fail the second.
    first_id = pending["items"][0]["id"]
    second_id = pending["items"][1]["id"]
    passed = client.post(f"/api/v1/rice-quality/{first_id}/pass")
    assert passed.status_code == 200
    assert passed.json()["rice_lot"]["reference"] == "RL-000001"

    failed = client.post(
        f"/api/v1/rice-quality/{second_id}/fail", json={"notes": "too much broken"}
    )
    assert failed.json()["status"] == "FAILED"

    # Only the passed output became a rice lot with stock.
    lots = client.get("/api/v1/rice-lots").json()
    assert lots["total"] == 1
    assert Decimal(str(lots["items"][0]["available_kg"])) == Decimal("3000.000")


# --------------------------------------------------------------------------- #
# Overspend guard
# --------------------------------------------------------------------------- #
def test_start_cannot_overspend_paddy(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)  # 8000 available

    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "9000.000"}]},
    ).json()

    resp = client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "insufficient_stock"
    # Stock untouched; batch still DRAFT.
    assert _available(client, lot_id) == Decimal("8000.000")
    assert client.get(f"/api/v1/milling-batches/{batch['id']}").json()["status"] == "DRAFT"


# --------------------------------------------------------------------------- #
# State machine guards
# --------------------------------------------------------------------------- #
def test_cannot_produce_before_start(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "1000.000"}]},
    ).json()
    resp = client.post(
        f"/api/v1/milling-batches/{batch['id']}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "10.000", "bag_weight_kg": "5.000"}
            ]
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_double_start_prevented(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "2000.000"}]},
    ).json()
    assert client.post(f"/api/v1/milling-batches/{batch['id']}/start").status_code == 200
    assert client.post(f"/api/v1/milling-batches/{batch['id']}/start").status_code == 409
    # Consumed exactly once.
    assert _available(client, lot_id) == Decimal("6000.000")


def test_complete_requires_production(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "1000.000"}]},
    ).json()
    client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    resp = client.post(f"/api/v1/milling-batches/{batch['id']}/complete")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_batch_with_unknown_paddy_lot_is_404(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    resp = client.post(
        "/api/v1/milling-batches",
        json={
            "inputs": [
                {"paddy_lot_id": "00000000-0000-0000-0000-000000000000", "quantity_kg": "1.000"}
            ]
        },
    )
    assert resp.status_code == 404


def test_bag_count_floor_division(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "7000.000"}]},
    ).json()
    client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    production = client.post(
        f"/api/v1/milling-batches/{batch['id']}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "6500.000", "bag_weight_kg": "50.000"}
            ]
        },
    ).json()
    assert production["outputs"][0]["bag_count"] == 130  # 6500 / 50


# --------------------------------------------------------------------------- #
# RBAC
# --------------------------------------------------------------------------- #
def test_staff_can_mill_but_not_pass_qc(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)

    # Staff runs the milling operations.
    client.cookies.clear()
    _login(client, "staff", "staff-passphrase-1")
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "1000.000"}]},
    )
    assert batch.status_code == 201
    batch_id = batch.json()["id"]
    assert client.post(f"/api/v1/milling-batches/{batch_id}/start").status_code == 200
    prod = client.post(
        f"/api/v1/milling-batches/{batch_id}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "900.000", "bag_weight_kg": "50.000"}
            ]
        },
    )
    assert prod.status_code == 201

    quality_id = client.get("/api/v1/rice-quality?status=PENDING").json()["items"][0]["id"]
    # Staff lacks rice.qc.approve.
    assert client.post(f"/api/v1/rice-quality/{quality_id}/pass").status_code == 403


# --------------------------------------------------------------------------- #
# Failed QC creates no stock
# --------------------------------------------------------------------------- #
def test_failed_qc_creates_no_rice_lot_or_stock(client, make_user) -> None:
    _users(make_user)
    _login(client, "owner", "owner-passphrase-1")
    lot_id = _accepted_paddy_lot(client)
    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": lot_id, "quantity_kg": "1000.000"}]},
    ).json()
    client.post(f"/api/v1/milling-batches/{batch['id']}/start")
    client.post(
        f"/api/v1/milling-batches/{batch['id']}/productions",
        json={
            "outputs": [
                {"category": "CATEGORY_1", "quantity_kg": "900.000", "bag_weight_kg": "50.000"}
            ]
        },
    )
    quality_id = client.get("/api/v1/rice-quality?status=PENDING").json()["items"][0]["id"]
    client.post(f"/api/v1/rice-quality/{quality_id}/fail")

    assert client.get("/api/v1/rice-lots").json()["total"] == 0
    with SessionLocal() as db:
        rice_moves = [
            t
            for t in db.execute(select(InventoryTransaction)).scalars().all()
            if t.transaction_type == "RICE_PRODUCTION"
        ]
        assert rice_moves == []
