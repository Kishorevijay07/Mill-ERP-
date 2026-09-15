"""create milling and rice tables

Revision ID: 5c35df2cd0f2
Revises: 2fce8c3f4318
Create Date: 2026-09-04 06:19:09.373723+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c35df2cd0f2"
down_revision: str | None = "2fce8c3f4318"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "milling_batches",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'DRAFT'"), nullable=False
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milling_batches")),
        sa.UniqueConstraint("reference", name=op.f("uq_milling_batches_reference")),
    )
    op.create_index(op.f("ix_milling_batches_status"), "milling_batches", ["status"], unique=False)
    op.create_table(
        "rice_productions",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("produced_on", sa.Date(), nullable=True),
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
            ["batch_id"],
            ["milling_batches.id"],
            name=op.f("fk_rice_productions_batch_id_milling_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rice_productions")),
        sa.UniqueConstraint("reference", name=op.f("uq_rice_productions_reference")),
    )
    op.create_index(
        op.f("ix_rice_productions_batch_id"), "rice_productions", ["batch_id"], unique=False
    )
    op.create_table(
        "rice_production_outputs",
        sa.Column("production_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("bag_weight_kg", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("bag_count", sa.Integer(), nullable=False),
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
            "bag_count >= 0", name=op.f("ck_rice_production_outputs_bag_count_non_negative")
        ),
        sa.CheckConstraint(
            "bag_weight_kg > 0", name=op.f("ck_rice_production_outputs_bag_weight_positive")
        ),
        sa.CheckConstraint(
            "quantity_kg > 0", name=op.f("ck_rice_production_outputs_quantity_positive")
        ),
        sa.ForeignKeyConstraint(
            ["production_id"],
            ["rice_productions.id"],
            name=op.f("fk_rice_production_outputs_production_id_rice_productions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rice_production_outputs")),
    )
    op.create_index(
        op.f("ix_rice_production_outputs_production_id"),
        "rice_production_outputs",
        ["production_id"],
        unique=False,
    )
    op.create_table(
        "rice_lots",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("output_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("bag_weight_kg", sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column("bag_count", sa.Integer(), nullable=False),
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
        sa.CheckConstraint("bag_count >= 0", name=op.f("ck_rice_lots_bag_count_non_negative")),
        sa.CheckConstraint("bag_weight_kg > 0", name=op.f("ck_rice_lots_bag_weight_positive")),
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_rice_lots_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["output_id"],
            ["rice_production_outputs.id"],
            name=op.f("fk_rice_lots_output_id_rice_production_outputs"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rice_lots")),
        sa.UniqueConstraint("output_id", name=op.f("uq_rice_lots_output_id")),
        sa.UniqueConstraint("reference", name=op.f("uq_rice_lots_reference")),
    )
    op.create_index(op.f("ix_rice_lots_category"), "rice_lots", ["category"], unique=False)
    op.create_table(
        "rice_quality",
        sa.Column("output_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'PENDING'"), nullable=False
        ),
        sa.Column("broken_pct", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("moisture_pct", sa.Numeric(precision=5, scale=2), nullable=True),
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
            "broken_pct IS NULL OR (broken_pct >= 0 AND broken_pct <= 100)",
            name=op.f("ck_rice_quality_broken_range"),
        ),
        sa.CheckConstraint(
            "moisture_pct IS NULL OR (moisture_pct >= 0 AND moisture_pct <= 100)",
            name=op.f("ck_rice_quality_moisture_range"),
        ),
        sa.ForeignKeyConstraint(
            ["output_id"],
            ["rice_production_outputs.id"],
            name=op.f("fk_rice_quality_output_id_rice_production_outputs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rice_quality")),
        sa.UniqueConstraint("output_id", name=op.f("uq_rice_quality_output_id")),
    )
    op.create_index(op.f("ix_rice_quality_status"), "rice_quality", ["status"], unique=False)
    op.create_table(
        "milling_inputs",
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("paddy_lot_id", sa.Uuid(), nullable=False),
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
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_milling_inputs_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["milling_batches.id"],
            name=op.f("fk_milling_inputs_batch_id_milling_batches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["paddy_lot_id"],
            ["paddy_lots.id"],
            name=op.f("fk_milling_inputs_paddy_lot_id_paddy_lots"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_milling_inputs")),
        sa.UniqueConstraint("batch_id", "paddy_lot_id", name="batch_paddy_lot"),
    )
    op.create_index(
        op.f("ix_milling_inputs_batch_id"), "milling_inputs", ["batch_id"], unique=False
    )
    op.create_index(
        op.f("ix_milling_inputs_paddy_lot_id"), "milling_inputs", ["paddy_lot_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_milling_inputs_paddy_lot_id"), table_name="milling_inputs")
    op.drop_index(op.f("ix_milling_inputs_batch_id"), table_name="milling_inputs")
    op.drop_table("milling_inputs")
    op.drop_index(op.f("ix_rice_quality_status"), table_name="rice_quality")
    op.drop_table("rice_quality")
    op.drop_index(op.f("ix_rice_lots_category"), table_name="rice_lots")
    op.drop_table("rice_lots")
    op.drop_index(
        op.f("ix_rice_production_outputs_production_id"), table_name="rice_production_outputs"
    )
    op.drop_table("rice_production_outputs")
    op.drop_index(op.f("ix_rice_productions_batch_id"), table_name="rice_productions")
    op.drop_table("rice_productions")
    op.drop_index(op.f("ix_milling_batches_status"), table_name="milling_batches")
    op.drop_table("milling_batches")
