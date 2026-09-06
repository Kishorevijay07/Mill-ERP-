"""Government claim invoice rendering (fpdf2 -> PDF bytes).

Core fonts are latin-1 only, so currency is shown as a code/"Rs." rather than a
unicode symbol. The invoice carries the covered delivery references for
traceability from claim back to the dispatches/receipts it bills.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fpdf import FPDF

from app.modules.billing.models import ClaimLine, GovernmentClaim
from app.modules.government.models import GovernmentAgency
from app.modules.settings.models import MillSettings


@dataclass(frozen=True)
class InvoiceContext:
    mill: MillSettings
    agency: GovernmentAgency
    claim: GovernmentClaim
    lines: list[ClaimLine]
    receipt_refs: list[str]
    paid: Decimal
    outstanding: Decimal


def _money(value: Decimal) -> str:
    return f"{value:,.2f}"


def render_claim_invoice(ctx: InvoiceContext) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    cur = ctx.mill.currency or "INR"

    # ---- Mill header ----
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, ctx.mill.name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for part in (ctx.mill.address, ctx.mill.registration_no, ctx.mill.contact_phone):
        if part:
            pdf.cell(0, 5, str(part), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "GOVERNMENT CLAIM / INVOICE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Invoice No: {ctx.claim.reference}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Status: {ctx.claim.status}", new_x="LMARGIN", new_y="NEXT")

    # ---- Bill to ----
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"{ctx.agency.code} - {ctx.agency.name}", new_x="LMARGIN", new_y="NEXT")

    # ---- Line table ----
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    widths = (95, 25, 30, 30)
    headers = ("Description", "Quantity", "Rate", f"Amount ({cur})")
    for w, h in zip(widths, headers, strict=True):
        pdf.cell(w, 7, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for line in sorted(ctx.lines, key=lambda x: x.sort_order):
        label = ("(-) " if line.is_deduction else "") + line.description
        pdf.cell(widths[0], 7, label[:60], border=1)
        pdf.cell(widths[1], 7, f"{line.quantity:,.3f}", border=1, align="R")
        pdf.cell(widths[2], 7, f"{line.rate:,.4f}", border=1, align="R")
        amount = -line.amount if line.is_deduction else line.amount
        pdf.cell(widths[3], 7, _money(amount), border=1, align="R")
        pdf.ln()

    # ---- Totals ----
    label_w = widths[0] + widths[1] + widths[2]
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(label_w, 7, "Gross", border=1, align="R")
    pdf.cell(widths[3], 7, _money(ctx.claim.gross_amount), border=1, align="R")
    pdf.ln()
    pdf.cell(label_w, 7, "Deductions", border=1, align="R")
    pdf.cell(widths[3], 7, _money(ctx.claim.deduction_amount), border=1, align="R")
    pdf.ln()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(label_w, 8, f"Net Payable ({cur})", border=1, align="R")
    pdf.cell(widths[3], 8, _money(ctx.claim.net_amount), border=1, align="R")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(label_w, 7, "Paid", border=1, align="R")
    pdf.cell(widths[3], 7, _money(ctx.paid), border=1, align="R")
    pdf.ln()
    pdf.cell(label_w, 7, "Outstanding", border=1, align="R")
    pdf.cell(widths[3], 7, _money(ctx.outstanding), border=1, align="R")
    pdf.ln()

    # ---- Traceability footer ----
    if ctx.receipt_refs:
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(0, 5, "Covers delivery receipts: " + ", ".join(ctx.receipt_refs))
    if ctx.mill.invoice_notes:
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(0, 5, ctx.mill.invoice_notes)

    return bytes(pdf.output())
