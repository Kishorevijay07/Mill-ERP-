"""create settings, documents, billing tables

Revision ID: 378f115e5adc
Revises: c3b3e9540838
Create Date: 2026-09-04 07:25:45.441494+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "378f115e5adc"
down_revision: str | None = "c3b3e9540838"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "charge_rates",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("rate", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("is_deduction", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint("rate >= 0", name=op.f("ck_charge_rates_rate_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_charge_rates")),
        sa.UniqueConstraint("code", name=op.f("uq_charge_rates_code")),
    )
    op.create_table(
        "documents",
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index(op.f("ix_documents_entity_id"), "documents", ["entity_id"], unique=False)
    op.create_index(op.f("ix_documents_entity_type"), "documents", ["entity_type"], unique=False)
    op.create_table(
        "mill_settings",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=1000), nullable=True),
        sa.Column("registration_no", sa.String(length=64), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("invoice_notes", sa.String(length=2000), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mill_settings")),
    )
    op.create_table(
        "government_claims",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'DRAFT'"), nullable=False
        ),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("gross_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("deduction_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("net_amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "deduction_amount >= 0", name=op.f("ck_government_claims_deduction_non_negative")
        ),
        sa.CheckConstraint(
            "gross_amount >= 0", name=op.f("ck_government_claims_gross_non_negative")
        ),
        sa.CheckConstraint("net_amount >= 0", name=op.f("ck_government_claims_net_non_negative")),
        sa.ForeignKeyConstraint(
            ["agency_id"],
            ["government_agencies.id"],
            name=op.f("fk_government_claims_agency_id_government_agencies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_government_claims")),
        sa.UniqueConstraint("reference", name=op.f("uq_government_claims_reference")),
    )
    op.create_index(
        op.f("ix_government_claims_agency_id"), "government_claims", ["agency_id"], unique=False
    )
    op.create_index(
        op.f("ix_government_claims_status"), "government_claims", ["status"], unique=False
    )
    op.create_table(
        "claim_lines",
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("rate", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("is_deduction", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint("quantity >= 0", name=op.f("ck_claim_lines_quantity_non_negative")),
        sa.CheckConstraint("rate >= 0", name=op.f("ck_claim_lines_rate_non_negative")),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["government_claims.id"],
            name=op.f("fk_claim_lines_claim_id_government_claims"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim_lines")),
    )
    op.create_index(op.f("ix_claim_lines_claim_id"), "claim_lines", ["claim_id"], unique=False)
    op.create_table(
        "payments",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=True),
        sa.Column("method", sa.String(length=64), nullable=True),
        sa.Column("reference_no", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint("amount > 0", name=op.f("ck_payments_amount_positive")),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["government_claims.id"],
            name=op.f("fk_payments_claim_id_government_claims"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
        sa.UniqueConstraint("reference", name=op.f("uq_payments_reference")),
    )
    op.create_index(op.f("ix_payments_claim_id"), "payments", ["claim_id"], unique=False)
    op.create_table(
        "claim_deliveries",
        sa.Column("claim_id", sa.Uuid(), nullable=False),
        sa.Column("delivery_receipt_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["claim_id"],
            ["government_claims.id"],
            name=op.f("fk_claim_deliveries_claim_id_government_claims"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["delivery_receipt_id"],
            ["delivery_receipts.id"],
            name=op.f("fk_claim_deliveries_delivery_receipt_id_delivery_receipts"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_claim_deliveries")),
        sa.UniqueConstraint(
            "delivery_receipt_id", name=op.f("uq_claim_deliveries_delivery_receipt_id")
        ),
    )
    op.create_index(
        op.f("ix_claim_deliveries_claim_id"), "claim_deliveries", ["claim_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_claim_deliveries_claim_id"), table_name="claim_deliveries")
    op.drop_table("claim_deliveries")
    op.drop_index(op.f("ix_payments_claim_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_claim_lines_claim_id"), table_name="claim_lines")
    op.drop_table("claim_lines")
    op.drop_index(op.f("ix_government_claims_status"), table_name="government_claims")
    op.drop_index(op.f("ix_government_claims_agency_id"), table_name="government_claims")
    op.drop_table("government_claims")
    op.drop_table("mill_settings")
    op.drop_index(op.f("ix_documents_entity_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_entity_id"), table_name="documents")
    op.drop_table("documents")
    op.drop_table("charge_rates")
