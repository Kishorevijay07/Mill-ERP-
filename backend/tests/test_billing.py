"""Billing tests: claim creation from delivered receipts, server-side totals,
duplicate-claim prevention, submit/approve, invoice PDF, payments to PAID, and
the dashboard KPIs.
"""

from __future__ import annotations

from decimal import Decimal


def _login(client, identifier: str, password: str):
    return client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})


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


def _seed_rates() -> None:
    from app.core.database import SessionLocal
    from app.modules.settings.service import seed_default_charge_rates

    with SessionLocal() as db:
        seed_default_charge_rates(db)


def _delivered_receipt(client) -> dict[str, str]:
    """Drive the full chain (as owner) to a DELIVERED receipt of 2000 kg rice."""
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
    paddy_lot = client.get("/api/v1/paddy-lots").json()["items"][0]["id"]

    batch = client.post(
        "/api/v1/milling-batches",
        json={"inputs": [{"paddy_lot_id": paddy_lot, "quantity_kg": "5000.000"}]},
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
    rice_lot = client.post(f"/api/v1/rice-quality/{quality_id}/pass").json()["rice_lot"]["id"]

    dispatch = client.post(
        "/api/v1/dispatches",
        json={
            "destination_name": "Govt Warehouse",
            "lorry_number": "TN22",
            "items": [{"rice_lot_id": rice_lot, "quantity_kg": "2000.000"}],
        },
    ).json()
    client.post(f"/api/v1/dispatches/{dispatch['id']}/prepare")
    client.post(f"/api/v1/dispatches/{dispatch['id']}/dispatch")
    receipt = client.post(
        f"/api/v1/dispatches/{dispatch['id']}/delivery-receipt",
        json={"received_quantity_kg": "2000.000"},
    ).json()
    return {"agency_id": agency["id"], "receipt_id": receipt["id"]}


def _create_claim(client, agency_id: str, receipt_id: str):
    return client.post(
        "/api/v1/government-claims",
        json={"agency_id": agency_id, "delivery_receipt_ids": [receipt_id]},
    )


# --------------------------------------------------------------------------- #
# Claim creation + server-side totals
# --------------------------------------------------------------------------- #
def test_claim_autofills_lines_and_totals(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)

    resp = _create_claim(client, ctx["agency_id"], ctx["receipt_id"])
    assert resp.status_code == 201
    claim = resp.json()
    assert claim["reference"] == "CLM-000001"
    # 2000 kg: MILLING 1.5 = 3000, HANDLING 0.5 = 1000, GUNNY 0.1 = 200 deduction.
    assert Decimal(claim["gross_amount"]) == Decimal("4000.00")
    assert Decimal(claim["deduction_amount"]) == Decimal("200.00")
    assert Decimal(claim["net_amount"]) == Decimal("3800.00")
    assert len(claim["lines"]) == 3


def test_duplicate_claim_prevented(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    assert _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).status_code == 201
    dup = _create_claim(client, ctx["agency_id"], ctx["receipt_id"])
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "conflict"


def test_edit_lines_recomputes_totals(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    claim = _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).json()

    edited = client.put(
        f"/api/v1/government-claims/{claim['id']}/lines",
        json={
            "lines": [
                {
                    "description": "Custom milling",
                    "quantity": "2000.000",
                    "rate": "2.0000",
                    "is_deduction": False,
                },
                {
                    "description": "Deduction",
                    "quantity": "1.000",
                    "rate": "100.0000",
                    "is_deduction": True,
                },
            ]
        },
    )
    assert edited.status_code == 200
    body = edited.json()
    assert Decimal(body["gross_amount"]) == Decimal("4000.00")
    assert Decimal(body["deduction_amount"]) == Decimal("100.00")
    assert Decimal(body["net_amount"]) == Decimal("3900.00")


# --------------------------------------------------------------------------- #
# Lifecycle + invoice + payments
# --------------------------------------------------------------------------- #
def test_full_billing_to_paid_with_invoice(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    claim = _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).json()
    cid = claim["id"]

    assert client.post(f"/api/v1/government-claims/{cid}/submit").json()["status"] == "SUBMITTED"
    assert client.post(f"/api/v1/government-claims/{cid}/approve").json()["status"] == "APPROVED"

    # Generate + download the invoice PDF.
    invoice = client.post(f"/api/v1/government-claims/{cid}/invoice")
    assert invoice.status_code == 200
    doc_id = invoice.json()["document_id"]
    download = client.get(f"/api/v1/documents/{doc_id}/download")
    assert download.status_code == 200
    assert download.content[:5] == b"%PDF-"

    # Partial then final payment -> PAID.
    p1 = client.post("/api/v1/payments", json={"claim_id": cid, "amount": "1800.00"})
    assert p1.status_code == 201
    assert client.get(f"/api/v1/government-claims/{cid}").json()["status"] == "PARTIALLY_PAID"

    p2 = client.post("/api/v1/payments", json={"claim_id": cid, "amount": "2000.00"})
    assert p2.status_code == 201
    detail = client.get(f"/api/v1/government-claims/{cid}").json()
    assert detail["status"] == "PAID"
    assert Decimal(detail["outstanding_amount"]) == Decimal("0.00")


def test_payment_cannot_exceed_outstanding(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    claim = _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).json()
    cid = claim["id"]
    client.post(f"/api/v1/government-claims/{cid}/submit")
    client.post(f"/api/v1/government-claims/{cid}/approve")

    over = client.post("/api/v1/payments", json={"claim_id": cid, "amount": "5000.00"})
    assert over.status_code == 409
    assert over.json()["error"]["code"] == "overpayment"


def test_payment_requires_approved_claim(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    claim = _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).json()
    # DRAFT claim -> payment refused.
    resp = client.post("/api/v1/payments", json={"claim_id": claim["id"], "amount": "10.00"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


def test_duplicate_payment_reference_prevented(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)
    claim = _create_claim(client, ctx["agency_id"], ctx["receipt_id"]).json()
    cid = claim["id"]
    client.post(f"/api/v1/government-claims/{cid}/submit")
    client.post(f"/api/v1/government-claims/{cid}/approve")

    first = client.post(
        "/api/v1/payments", json={"claim_id": cid, "amount": "1000.00", "reference_no": "TXN-1"}
    )
    assert first.status_code == 201
    dup = client.post(
        "/api/v1/payments", json={"claim_id": cid, "amount": "1000.00", "reference_no": "TXN-1"}
    )
    assert dup.status_code == 409


# --------------------------------------------------------------------------- #
# RBAC + dashboard
# --------------------------------------------------------------------------- #
def test_staff_cannot_create_claim(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    ctx = _delivered_receipt(client)

    client.cookies.clear()
    _login(client, "staff", "staff-passphrase-1")
    resp = _create_claim(client, ctx["agency_id"], ctx["receipt_id"])
    assert resp.status_code == 403


def test_dashboard_kpis(client, make_user) -> None:
    _users(make_user)
    _seed_rates()
    _login(client, "owner", "owner-passphrase-1")
    _delivered_receipt(client)

    resp = client.get("/api/v1/reports/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body).issuperset(
        {
            "paddy_received_kg",
            "paddy_available_kg",
            "rice_stock_kg",
            "pending_delivery",
            "claims_pending",
            "amount_paid",
            "amount_outstanding",
        }
    )
    # 8000 received, 5000 consumed -> 3000 paddy available.
    assert Decimal(body["paddy_available_kg"]) == Decimal("3000.000")
    # 3000 rice produced, 2000 dispatched -> 1000 rice stock.
    assert Decimal(body["rice_stock_kg"]) == Decimal("1000.000")
