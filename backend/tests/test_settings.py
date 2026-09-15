"""Settings tests: mill profile + charge-rate CRUD and RBAC."""

from __future__ import annotations


def _login(client, identifier: str, password: str):
    return client.post("/api/v1/auth/login", json={"identifier": identifier, "password": password})


def _users(make_user) -> None:
    make_user(
        email="admin@example.com",
        username="admin",
        password="admin-passphrase-1",
        role_codes=("ADMIN",),
        is_superuser=True,
    )
    make_user(
        email="owner@example.com",
        username="owner",
        password="owner-passphrase-1",
        role_codes=("OWNER",),
    )


def test_mill_settings_get_creates_default_and_update(client, make_user) -> None:
    _users(make_user)
    _login(client, "admin", "admin-passphrase-1")

    got = client.get("/api/v1/mill-settings")
    assert got.status_code == 200
    assert got.json()["currency"] == "INR"

    updated = client.put(
        "/api/v1/mill-settings",
        json={"name": "KKM Rice Mill", "currency": "INR", "registration_no": "REG-1"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "KKM Rice Mill"


def test_charge_rate_crud(client, make_user) -> None:
    _users(make_user)
    _login(client, "admin", "admin-passphrase-1")

    created = client.post(
        "/api/v1/charge-rates",
        json={"code": "MILLING", "label": "Milling charge", "rate": "1.5000", "unit": "PER_KG"},
    )
    assert created.status_code == 201
    rate_id = created.json()["id"]

    # Duplicate code -> 409.
    dup = client.post(
        "/api/v1/charge-rates",
        json={"code": "MILLING", "label": "x", "rate": "1.0000", "unit": "PER_KG"},
    )
    assert dup.status_code == 409

    updated = client.put(
        f"/api/v1/charge-rates/{rate_id}",
        json={
            "label": "Milling charge",
            "rate": "2.0000",
            "unit": "PER_KG",
            "is_deduction": False,
            "is_active": True,
        },
    )
    assert updated.json()["rate"] == "2.0000"

    assert client.get("/api/v1/charge-rates").json()[0]["code"] == "MILLING"
    assert client.delete(f"/api/v1/charge-rates/{rate_id}").status_code == 204
    assert client.get("/api/v1/charge-rates").json() == []


def test_settings_rbac(client, make_user) -> None:
    _users(make_user)
    # Owner can view but not manage.
    _login(client, "owner", "owner-passphrase-1")
    assert client.get("/api/v1/charge-rates").status_code == 200
    assert (
        client.post(
            "/api/v1/charge-rates",
            json={"code": "X", "label": "X", "rate": "1.0000", "unit": "PER_KG"},
        ).status_code
        == 403
    )


def test_settings_requires_auth(client) -> None:
    assert client.get("/api/v1/mill-settings").status_code == 401
