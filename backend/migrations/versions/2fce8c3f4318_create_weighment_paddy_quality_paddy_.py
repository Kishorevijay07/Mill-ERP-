"""create weighment, paddy quality, paddy lot, inventory tables

Revision ID: 2fce8c3f4318
Revises: f370df7a03c4
Create Date: 2026-09-03 20:22:47.179263+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2fce8c3f4318"
down_revision: str | None = "f370df7a03c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventory_transactions",
        sa.Column("item_type", sa.String(length=16), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("transaction_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inventory_transactions")),
    )
    op.create_index(
        "ix_inventory_transactions_item",
        "inventory_transactions",
        ["item_type", "item_id"],
        unique=False,
    )
    op.create_table(
        "paddy_lots",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("load_id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_paddy_lots_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["government_loads.id"],
            name=op.f("fk_paddy_lots_load_id_government_loads"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paddy_lots")),
        sa.UniqueConstraint("load_id", name=op.f("uq_paddy_lots_load_id")),
        sa.UniqueConstraint("reference", name=op.f("uq_paddy_lots_reference")),
    )
    op.create_table(
        "paddy_quality",
        sa.Column("load_id", sa.Uuid(), nullable=False),
        sa.Column("moisture_pct", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("foreign_matter_pct", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("damaged_pct", sa.Numeric(precision=5, scale=2), nullable=False),
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
            "damaged_pct >= 0 AND damaged_pct <= 100", name=op.f("ck_paddy_quality_damaged_range")
        ),
        sa.CheckConstraint(
            "foreign_matter_pct >= 0 AND foreign_matter_pct <= 100",
            name=op.f("ck_paddy_quality_foreign_matter_range"),
        ),
        sa.CheckConstraint(
            "moisture_pct >= 0 AND moisture_pct <= 100",
            name=op.f("ck_paddy_quality_moisture_range"),
        ),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["government_loads.id"],
            name=op.f("fk_paddy_quality_load_id_government_loads"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_paddy_quality")),
        sa.UniqueConstraint("load_id", name=op.f("uq_paddy_quality_load_id")),
    )
    op.create_table(
        "weighments",
        sa.Column("load_id", sa.Uuid(), nullable=False),
        sa.Column("gross_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("tare_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("net_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("is_final", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("weighbridge_ref", sa.String(length=64), nullable=True),
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
        sa.CheckConstraint("gross_kg > 0", name=op.f("ck_weighments_gross_positive")),
        sa.CheckConstraint("gross_kg > tare_kg", name=op.f("ck_weighments_gross_gt_tare")),
        sa.CheckConstraint("net_kg > 0", name=op.f("ck_weighments_net_positive")),
        sa.CheckConstraint("tare_kg >= 0", name=op.f("ck_weighments_tare_non_negative")),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["government_loads.id"],
            name=op.f("fk_weighments_load_id_government_loads"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weighments")),
    )
    op.create_index("ix_weighments_load_id", "weighments", ["load_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_weighments_load_id", table_name="weighments")
    op.drop_table("weighments")
    op.drop_table("paddy_quality")
    op.drop_table("paddy_lots")
    op.drop_index("ix_inventory_transactions_item", table_name="inventory_transactions")
    op.drop_table("inventory_transactions")
