"""Foundation tests: liveness, readiness contract, and the safe error shape."""

from __future__ import annotations


def test_health_ok(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"]
    assert body["version"]


def test_ready_reports_dependencies(client) -> None:
    # No Postgres is running in unit CI, so readiness should report not-ready
    # with a database dependency entry — and must never raise a 500.
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)
    body = resp.json()
    assert "dependencies" in body
    names = {dep["name"] for dep in body["dependencies"]}
    assert "database" in names


def test_unknown_route_uses_safe_error_contract(client) -> None:
    resp = client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert set(body["error"]).issuperset({"code", "message"})
