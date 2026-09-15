"""Unit tests for the reference-number generator and the audit log."""

from __future__ import annotations

from sqlalchemy import select

from app.shared.audit import AuditLog, record_audit
from app.shared.reference import ReferencePrefix, generate_reference


def test_reference_numbers_are_sequential_and_per_prefix(db_session) -> None:
    r1 = generate_reference(db_session, ReferencePrefix.ALLOCATION)
    r2 = generate_reference(db_session, ReferencePrefix.ALLOCATION)
    r3 = generate_reference(db_session, ReferencePrefix.LOAD)
    db_session.commit()

    assert r1 == "AL-000001"
    assert r2 == "AL-000002"
    # A different prefix has its own independent counter.
    assert r3 == "LD-000001"


def test_record_audit_appends_row(db_session) -> None:
    record_audit(
        db_session,
        action="test.action",
        entity_type="thing",
        entity_id="abc",
        after_data={"k": "v"},
    )
    db_session.commit()

    rows = db_session.execute(select(AuditLog)).scalars().all()
    assert len(rows) == 1
    assert rows[0].action == "test.action"
    assert rows[0].entity_type == "thing"
    assert rows[0].after_data == {"k": "v"}
