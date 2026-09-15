"""Billing HTTP endpoints: claims, lines, submit/approve, invoice, payments."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import actor_from_request as _actor
from app.modules.auth.dependencies import require_permission
from app.modules.auth.models import User
from app.modules.auth.permissions import Permission
from app.modules.billing import service
from app.modules.billing.models import GovernmentClaim
from app.modules.billing.schemas import (
    ClaimCreate,
    ClaimDetail,
    ClaimLineOut,
    ClaimLinesReplace,
    ClaimOut,
    InvoiceResponse,
    PaymentCreate,
    PaymentOut,
)
from app.shared.http import Pagination
from app.shared.schemas import Page

router = APIRouter(tags=["billing"])


def _detail(db: Session, claim: GovernmentClaim) -> ClaimDetail:
    paid = service.paid_amount(db, claim.id)
    outstanding = claim.net_amount - paid
    return ClaimDetail(
        **ClaimOut.model_validate(claim).model_dump(),
        lines=[ClaimLineOut.model_validate(line) for line in claim.lines],
        delivery_receipt_ids=service.delivery_receipt_ids(claim),
        payments=[PaymentOut.model_validate(p) for p in claim.payments],
        paid_amount=paid,
        outstanding_amount=outstanding,
    )


@router.post("/government-claims", response_model=ClaimDetail, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.BILLING_CREATE)),
) -> ClaimDetail:
    claim = service.create_claim(db, payload, _actor(request, user))
    return _detail(db, claim)


@router.get("/government-claims", response_model=Page[ClaimOut])
def list_claims(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.BILLING_VIEW)),
) -> Page[ClaimOut]:
    rows, total = service.list_claims(db, pagination.page, pagination.page_size)
    return Page[ClaimOut](
        items=[ClaimOut.model_validate(r) for r in rows],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/government-claims/{claim_id}", response_model=ClaimDetail)
def get_claim(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.BILLING_VIEW)),
) -> ClaimDetail:
    return _detail(db, service.get_claim(db, claim_id))


@router.put("/government-claims/{claim_id}/lines", response_model=ClaimDetail)
def replace_lines(
    claim_id: uuid.UUID,
    payload: ClaimLinesReplace,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.BILLING_CREATE)),
) -> ClaimDetail:
    claim = service.replace_lines(db, claim_id, payload.lines, _actor(request, user))
    return _detail(db, claim)


@router.post("/government-claims/{claim_id}/submit", response_model=ClaimDetail)
def submit_claim(
    claim_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.BILLING_SUBMIT)),
) -> ClaimDetail:
    return _detail(db, service.submit_claim(db, claim_id, _actor(request, user)))


@router.post("/government-claims/{claim_id}/approve", response_model=ClaimDetail)
def approve_claim(
    claim_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.BILLING_APPROVE)),
) -> ClaimDetail:
    return _detail(db, service.approve_claim(db, claim_id, _actor(request, user)))


@router.post("/government-claims/{claim_id}/invoice", response_model=InvoiceResponse)
def generate_invoice(
    claim_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.BILLING_CREATE)),
) -> InvoiceResponse:
    document = service.generate_invoice(db, claim_id, _actor(request, user))
    return InvoiceResponse(document_id=document.id, filename=document.filename)


@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.PAYMENT_RECORD)),
) -> PaymentOut:
    payment = service.record_payment(db, payload, _actor(request, user))
    return PaymentOut.model_validate(payment)


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    claim_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _user: User = Depends(require_permission(Permission.BILLING_VIEW)),
) -> list[PaymentOut]:
    rows = service.list_payments(db, claim_id)
    return [PaymentOut.model_validate(p) for p in rows]
