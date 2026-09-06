"""create dispatch and delivery tables

Revision ID: c3b3e9540838
Revises: 5c35df2cd0f2
Create Date: 2026-09-04 06:30:58.449249+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3b3e9540838"
down_revision: str | None = "5c35df2cd0f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dispatches",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'DRAFT'"), nullable=False
        ),
        sa.Column("destination_name", sa.String(length=255), nullable=False),
        sa.Column("destination_agency_id", sa.Uuid(), nullable=True),
        sa.Column("delivery_order_id", sa.Uuid(), nullable=True),
        sa.Column("lorry_number", sa.String(length=32), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["delivery_order_id"],
            ["delivery_orders.id"],
            name=op.f("fk_dispatches_delivery_order_id_delivery_orders"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["destination_agency_id"],
            ["government_agencies.id"],
            name=op.f("fk_dispatches_destination_agency_id_government_agencies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dispatches")),
        sa.UniqueConstraint("reference", name=op.f("uq_dispatches_reference")),
    )
    op.create_index(
        op.f("ix_dispatches_delivery_order_id"), "dispatches", ["delivery_order_id"], unique=False
    )
    op.create_index(op.f("ix_dispatches_status"), "dispatches", ["status"], unique=False)
    op.create_table(
        "delivery_receipts",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("dispatch_id", sa.Uuid(), nullable=False),
        sa.Column("dispatched_quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("received_quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("received_bags", sa.Integer(), nullable=True),
        sa.Column("shortage_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("excess_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("receipt_number", sa.String(length=64), nullable=True),
        sa.Column("receipt_date", sa.Date(), nullable=True),
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
        sa.CheckConstraint("excess_kg >= 0", name=op.f("ck_delivery_receipts_excess_non_negative")),
        sa.CheckConstraint(
            "received_quantity_kg >= 0", name=op.f("ck_delivery_receipts_received_non_negative")
        ),
        sa.CheckConstraint(
            "shortage_kg >= 0", name=op.f("ck_delivery_receipts_shortage_non_negative")
        ),
        sa.ForeignKeyConstraint(
            ["dispatch_id"],
            ["dispatches.id"],
            name=op.f("fk_delivery_receipts_dispatch_id_dispatches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_receipts")),
        sa.UniqueConstraint("dispatch_id", name=op.f("uq_delivery_receipts_dispatch_id")),
        sa.UniqueConstraint("reference", name=op.f("uq_delivery_receipts_reference")),
    )
    op.create_table(
        "dispatch_items",
        sa.Column("dispatch_id", sa.Uuid(), nullable=False),
        sa.Column("rice_lot_id", sa.Uuid(), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
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
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_dispatch_items_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["dispatch_id"],
            ["dispatches.id"],
            name=op.f("fk_dispatch_items_dispatch_id_dispatches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["rice_lot_id"],
            ["rice_lots.id"],
            name=op.f("fk_dispatch_items_rice_lot_id_rice_lots"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dispatch_items")),
        sa.UniqueConstraint("dispatch_id", "rice_lot_id", name="dispatch_rice_lot"),
    )
    op.create_index(
        op.f("ix_dispatch_items_dispatch_id"), "dispatch_items", ["dispatch_id"], unique=False
    )
    op.create_index(
        op.f("ix_dispatch_items_rice_lot_id"), "dispatch_items", ["rice_lot_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_dispatch_items_rice_lot_id"), table_name="dispatch_items")
    op.drop_index(op.f("ix_dispatch_items_dispatch_id"), table_name="dispatch_items")
    op.drop_table("dispatch_items")
    op.drop_table("delivery_receipts")
    op.drop_index(op.f("ix_dispatches_status"), table_name="dispatches")
    op.drop_index(op.f("ix_dispatches_delivery_order_id"), table_name="dispatches")
    op.drop_table("dispatches")
