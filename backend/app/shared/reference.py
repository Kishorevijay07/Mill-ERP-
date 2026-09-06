"""Human-readable business reference numbers (AL-000001, DO-000001, ...).

Reference numbers are user-facing transaction identifiers — never primary keys
(ADR-0003). They are allocated from a per-prefix counter row that is locked for
the duration of the enclosing transaction, so concurrent callers cannot produce
duplicates. Allocation shares the caller's transaction, so a rollback also rolls
back the counter (no gaps from failed operations).
"""

from __future__ import annotations

from enum import StrEnum

from sqlalchemy import BigInteger, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.shared.base_model import Base


class ReferencePrefix(StrEnum):
    ALLOCATION = "AL"
    DELIVERY_ORDER = "DO"
    LOAD = "LD"
    PADDY_LOT = "PL"
    MILLING_BATCH = "MB"
    RICE_PRODUCTION = "RP"
    RICE_LOT = "RL"
    DISPATCH = "DEL"
    DELIVERY_RECEIPT = "REC"
    CLAIM = "CLM"
    PAYMENT = "PAY"


class ReferenceCounter(Base):
    __tablename__ = "reference_counters"

    prefix: Mapped[str] = mapped_column(String(8), primary_key=True)
    # The next value to be issued for this prefix.
    next_value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)


def generate_reference(db: Session, prefix: ReferencePrefix | str, *, width: int = 6) -> str:
    """Allocate the next reference number for ``prefix`` within ``db``'s transaction.

    Does not commit — the caller commits alongside the entity it is naming, so the
    reference and the record are created atomically.
    """
    prefix_value = str(prefix)
    counter = db.execute(
        select(ReferenceCounter).where(ReferenceCounter.prefix == prefix_value).with_for_update()
    ).scalar_one_or_none()

    if counter is None:
        counter = ReferenceCounter(prefix=prefix_value, next_value=1)
        db.add(counter)
        db.flush()

    value = counter.next_value
    counter.next_value = value + 1
    db.flush()
    return f"{prefix_value}-{value:0{width}d}"
