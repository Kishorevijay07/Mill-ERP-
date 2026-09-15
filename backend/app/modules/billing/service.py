"""Billing domain logic: claims, line generation, totals, and payments.

Rules (docs/BUSINESS-FLOW & TESTING):
- Claims cover only DELIVERED receipts not already claimed (duplicate-claim
  prevention via the unique claim_deliveries link).
- Totals (gross/deduction/net) are always computed server-side from the lines.
- Payments cannot exceed the outstanding balance; the last payment flips the claim
  to PAID, partial payments to PARTIALLY_PAID.
- All money is Decimal, quantized to 2 places — never float.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.billing.invoice import InvoiceContext, render_claim_invoice
from app.modules.billing.models import (
    ClaimDelivery,
    ClaimLine,
    ClaimStatus,
    GovernmentClaim,
    Payment,
)
from app.modules.billing.schemas import ClaimCreate, ClaimLineInput, PaymentCreate
from app.modules.delivery.models import DeliveryReceipt, Dispatch, DispatchStatus
from app.modules.documents.models import Document
from app.modules.documents.service import store_document
from app.modules.government.models import GovernmentAgency
from app.modules.settings.models import ChargeRate, ChargeUnit
from app.modules.settings.service import get_or_create_mill_settings
from app.shared.audit import record_audit
from app.shared.context import ActorContext
from app.shared.errors import ConflictError, DomainError, InvalidStateError, NotFoundError
from app.shared.reference import ReferencePrefix, generate_reference

_CLAIM_ENTITY = "government_claim"
_CENTS = Decimal("0.01")


class OverpaymentError(DomainError):
    code = "overpayment"
    status_code = 409


def _now() -> datetime:
    return datetime.now(UTC)


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def _load_claim(db: Session, claim_id: uuid.UUID) -> GovernmentClaim:
    claim = db.execute(
        select(GovernmentClaim)
        .options(
            selectinload(GovernmentClaim.lines),
            selectinload(GovernmentClaim.deliveries),
            selectinload(GovernmentClaim.payments),
        )
        .where(GovernmentClaim.id == claim_id)
    ).scalar_one_or_none()
    if claim is None:
        raise NotFoundError("Claim not found")
    return claim


def _recompute_totals(claim: GovernmentClaim) -> None:
    gross = sum((line.amount for line in claim.lines if not line.is_deduction), Decimal("0"))
    deduction = sum((line.amount for line in claim.lines if line.is_deduction), Decimal("0"))
    net = gross - deduction
    if net < 0:
        net = Decimal("0")
    claim.gross_amount = _money(gross)
    claim.deduction_amount = _money(deduction)
    claim.net_amount = _money(net)


def _line_basis(unit: str, billable_qty: Decimal) -> Decimal:
    if unit == ChargeUnit.PER_QUINTAL:
        return (billable_qty / Decimal("100")).quantize(Decimal("0.001"))
    if unit == ChargeUnit.FLAT:
        return Decimal("1")
    return billable_qty  # PER_KG


def paid_amount(db: Session, claim_id: uuid.UUID) -> Decimal:
    total = db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.claim_id == claim_id)
    ).scalar_one()
    return _money(Decimal(total))


# --------------------------------------------------------------------------- #
# Claims
# --------------------------------------------------------------------------- #
def create_claim(db: Session, data: ClaimCreate, actor: ActorContext) -> GovernmentClaim:
    if db.get(GovernmentAgency, data.agency_id) is None:
        raise NotFoundError("Agency not found")

    billable_qty = Decimal("0")
    for receipt_id in data.delivery_receipt_ids:
        receipt = db.get(DeliveryReceipt, receipt_id)
        if receipt is None:
            raise NotFoundError(f"Delivery receipt {receipt_id} not found")
        dispatch = db.get(Dispatch, receipt.dispatch_id)
        if dispatch is None or dispatch.status != DispatchStatus.DELIVERED:
            raise InvalidStateError("Only delivered dispatches can be claimed")
        if (
            db.execute(
                select(ClaimDelivery).where(ClaimDelivery.delivery_receipt_id == receipt_id)
            ).scalar_one_or_none()
            is not None
        ):
            raise ConflictError(f"Delivery receipt {receipt.reference} is already claimed")
        billable_qty += receipt.received_quantity_kg

    reference = generate_reference(db, ReferencePrefix.CLAIM)
    mill = get_or_create_mill_settings(db)
    claim = GovernmentClaim(
        reference=reference,
        agency_id=data.agency_id,
        status=ClaimStatus.DRAFT,
        currency=mill.currency,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(claim)
    db.flush()

    for receipt_id in data.delivery_receipt_ids:
        db.add(ClaimDelivery(claim_id=claim.id, delivery_receipt_id=receipt_id))

    # Auto-generate lines from active charge rates.
    active_rates = list(
        db.execute(
            select(ChargeRate).where(ChargeRate.is_active.is_(True)).order_by(ChargeRate.code)
        ).scalars()
    )
    for order, rate in enumerate(active_rates):
        quantity = _line_basis(rate.unit, billable_qty)
        amount = _money(quantity * rate.rate)
        db.add(
            ClaimLine(
                claim_id=claim.id,
                description=rate.label,
                quantity=quantity,
                rate=rate.rate,
                amount=amount,
                is_deduction=rate.is_deduction,
                sort_order=order,
                created_by=actor.user_id,
                updated_by=actor.user_id,
            )
        )
    db.flush()
    db.refresh(claim)
    _recompute_totals(claim)

    record_audit(
        db,
        action="government_claim.create",
        entity_type=_CLAIM_ENTITY,
        entity_id=claim.id,
        entity_reference=claim.reference,
        user_id=actor.user_id,
        after_data={
            "net_amount": str(claim.net_amount),
            "receipts": len(data.delivery_receipt_ids),
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _load_claim(db, claim.id)


def list_claims(db: Session, page: int, page_size: int) -> tuple[list[GovernmentClaim], int]:
    total = db.execute(select(func.count()).select_from(GovernmentClaim)).scalar_one()
    rows = list(
        db.execute(
            select(GovernmentClaim)
            .order_by(GovernmentClaim.reference)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars()
    )
    return rows, total


def get_claim(db: Session, claim_id: uuid.UUID) -> GovernmentClaim:
    return _load_claim(db, claim_id)


def replace_lines(
    db: Session, claim_id: uuid.UUID, lines: list[ClaimLineInput], actor: ActorContext
) -> GovernmentClaim:
    claim = _load_claim(db, claim_id)
    if claim.status != ClaimStatus.DRAFT:
        raise InvalidStateError("Claim lines can only be edited while DRAFT")

    for existing in list(claim.lines):
        db.delete(existing)
    db.flush()

    for order, item in enumerate(lines):
        db.add(
            ClaimLine(
                claim_id=claim.id,
                description=item.description,
                quantity=item.quantity,
                rate=item.rate,
                amount=_money(item.quantity * item.rate),
                is_deduction=item.is_deduction,
                sort_order=order,
                created_by=actor.user_id,
                updated_by=actor.user_id,
            )
        )
    db.flush()
    db.refresh(claim)
    _recompute_totals(claim)
    record_audit(
        db,
        action="government_claim.update_lines",
        entity_type=_CLAIM_ENTITY,
        entity_id=claim.id,
        entity_reference=claim.reference,
        user_id=actor.user_id,
        after_data={"net_amount": str(claim.net_amount), "lines": len(lines)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    return _load_claim(db, claim_id)


def submit_claim(db: Session, claim_id: uuid.UUID, actor: ActorContext) -> GovernmentClaim:
    claim = _load_claim(db, claim_id)
    if claim.status != ClaimStatus.DRAFT:
        raise InvalidStateError(f"Claim cannot be submitted from status {claim.status}")
    if not claim.lines:
        raise InvalidStateError("Claim has no lines")
    claim.status = ClaimStatus.SUBMITTED
    claim.submitted_at = _now()
    claim.updated_by = actor.user_id
    _audit_transition(db, claim, "government_claim.submit", ClaimStatus.DRAFT, actor)
    db.commit()
    return _load_claim(db, claim_id)


def approve_claim(db: Session, claim_id: uuid.UUID, actor: ActorContext) -> GovernmentClaim:
    claim = _load_claim(db, claim_id)
    if claim.status != ClaimStatus.SUBMITTED:
        raise InvalidStateError(f"Claim cannot be approved from status {claim.status}")
    claim.status = ClaimStatus.APPROVED
    claim.approved_at = _now()
    claim.updated_by = actor.user_id
    _audit_transition(db, claim, "government_claim.approve", ClaimStatus.SUBMITTED, actor)
    db.commit()
    return _load_claim(db, claim_id)


def _audit_transition(
    db: Session, claim: GovernmentClaim, action: str, before: str, actor: ActorContext
) -> None:
    record_audit(
        db,
        action=action,
        entity_type=_CLAIM_ENTITY,
        entity_id=claim.id,
        entity_reference=claim.reference,
        user_id=actor.user_id,
        before_data={"status": before},
        after_data={"status": claim.status},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )


# --------------------------------------------------------------------------- #
# Payments
# --------------------------------------------------------------------------- #
def record_payment(db: Session, data: PaymentCreate, actor: ActorContext) -> Payment:
    claim = _load_claim(db, data.claim_id)
    if claim.status not in (ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_PAID):
        raise InvalidStateError(
            f"Payments can only be recorded on an approved claim (status {claim.status})"
        )

    # Idempotency: a repeated reference_no on the same claim is refused.
    if (
        data.reference_no is not None
        and db.execute(
            select(Payment).where(
                Payment.claim_id == claim.id, Payment.reference_no == data.reference_no
            )
        ).scalar_one_or_none()
        is not None
    ):
        raise ConflictError("A payment with this reference number already exists")

    already_paid = paid_amount(db, claim.id)
    outstanding = _money(claim.net_amount - already_paid)
    if data.amount > outstanding:
        raise OverpaymentError(f"Payment {data.amount} exceeds outstanding balance {outstanding}")

    reference = generate_reference(db, ReferencePrefix.PAYMENT)
    payment = Payment(
        reference=reference,
        claim_id=claim.id,
        amount=data.amount,
        paid_on=data.paid_on,
        method=data.method,
        reference_no=data.reference_no,
        notes=data.notes,
        created_by=actor.user_id,
        updated_by=actor.user_id,
    )
    db.add(payment)
    db.flush()

    new_outstanding = _money(outstanding - data.amount)
    claim.status = ClaimStatus.PAID if new_outstanding <= 0 else ClaimStatus.PARTIALLY_PAID
    claim.updated_by = actor.user_id
    record_audit(
        db,
        action="payment.record",
        entity_type="payment",
        entity_id=payment.id,
        entity_reference=payment.reference,
        user_id=actor.user_id,
        after_data={
            "claim": claim.reference,
            "amount": str(data.amount),
            "claim_status": claim.status,
        },
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(payment)
    return payment


def list_payments(db: Session, claim_id: uuid.UUID | None = None) -> list[Payment]:
    stmt = select(Payment).order_by(Payment.reference)
    if claim_id is not None:
        stmt = stmt.where(Payment.claim_id == claim_id)
    return list(db.execute(stmt).scalars())


def delivery_receipt_ids(claim: GovernmentClaim) -> list[uuid.UUID]:
    return [link.delivery_receipt_id for link in claim.deliveries]


def generate_invoice(db: Session, claim_id: uuid.UUID, actor: ActorContext) -> Document:
    """Render the claim invoice to a PDF and store it as a document."""
    claim = _load_claim(db, claim_id)
    if not claim.lines:
        raise InvalidStateError("Cannot generate an invoice for a claim with no lines")

    agency = db.get(GovernmentAgency, claim.agency_id)
    if agency is None:
        raise NotFoundError("Agency not found")
    mill = get_or_create_mill_settings(db)

    receipt_ids = delivery_receipt_ids(claim)
    receipt_refs = list(
        db.execute(
            select(DeliveryReceipt.reference).where(DeliveryReceipt.id.in_(receipt_ids))
        ).scalars()
    )
    paid = paid_amount(db, claim.id)
    outstanding = _money(claim.net_amount - paid)

    pdf_bytes = render_claim_invoice(
        InvoiceContext(
            mill=mill,
            agency=agency,
            claim=claim,
            lines=list(claim.lines),
            receipt_refs=sorted(receipt_refs),
            paid=paid,
            outstanding=outstanding,
        )
    )
    document = store_document(
        db,
        entity_type=_CLAIM_ENTITY,
        entity_id=claim.id,
        filename=f"invoice-{claim.reference}.pdf",
        content_type="application/pdf",
        data=pdf_bytes,
        key_prefix="invoices",
        extension="pdf",
        created_by=actor.user_id,
    )
    record_audit(
        db,
        action="government_claim.invoice",
        entity_type=_CLAIM_ENTITY,
        entity_id=claim.id,
        entity_reference=claim.reference,
        user_id=actor.user_id,
        after_data={"document_id": str(document.id)},
        request_id=actor.request_id,
        ip_address=actor.ip_address,
    )
    db.commit()
    db.refresh(document)
    return document
