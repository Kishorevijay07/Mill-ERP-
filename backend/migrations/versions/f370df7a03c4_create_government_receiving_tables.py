"""create government receiving tables

Revision ID: f370df7a03c4
Revises: 7a8bc6ff6b30
Create Date: 2026-09-03 19:52:56.370245+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f370df7a03c4"
down_revision: str | None = "7a8bc6ff6b30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("entity_reference", sa.String(length=64), nullable=True),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_table(
        "government_agencies",
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_government_agencies")),
        sa.UniqueConstraint("code", name=op.f("uq_government_agencies_code")),
    )
    op.create_table(
        "reference_counters",
        sa.Column("prefix", sa.String(length=8), nullable=False),
        sa.Column("next_value", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("prefix", name=op.f("pk_reference_counters")),
    )
    op.create_table(
        "allocations",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("season", sa.String(length=64), nullable=True),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("allocated_on", sa.Date(), nullable=False),
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
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_allocations_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["agency_id"],
            ["government_agencies.id"],
            name=op.f("fk_allocations_agency_id_government_agencies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_allocations")),
        sa.UniqueConstraint("reference", name=op.f("uq_allocations_reference")),
    )
    op.create_index(op.f("ix_allocations_agency_id"), "allocations", ["agency_id"], unique=False)
    op.create_table(
        "delivery_orders",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("allocation_id", sa.Uuid(), nullable=False),
        sa.Column("do_number", sa.String(length=64), nullable=False),
        sa.Column("quantity_kg", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
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
        sa.CheckConstraint("quantity_kg > 0", name=op.f("ck_delivery_orders_quantity_positive")),
        sa.ForeignKeyConstraint(
            ["allocation_id"],
            ["allocations.id"],
            name=op.f("fk_delivery_orders_allocation_id_allocations"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_orders")),
        sa.UniqueConstraint("reference", name=op.f("uq_delivery_orders_reference")),
    )
    op.create_index(
        op.f("ix_delivery_orders_allocation_id"), "delivery_orders", ["allocation_id"], unique=False
    )
    op.create_table(
        "government_loads",
        sa.Column("reference", sa.String(length=32), nullable=False),
        sa.Column("delivery_order_id", sa.Uuid(), nullable=False),
        sa.Column("lorry_number", sa.String(length=32), nullable=False),
        sa.Column("driver_name", sa.String(length=255), nullable=True),
        sa.Column("declared_quantity_kg", sa.Numeric(precision=14, scale=3), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'DRAFT'"), nullable=False
        ),
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
            "declared_quantity_kg IS NULL OR declared_quantity_kg > 0",
            name=op.f("ck_government_loads_declared_quantity_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["delivery_order_id"],
            ["delivery_orders.id"],
            name=op.f("fk_government_loads_delivery_order_id_delivery_orders"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_government_loads")),
        sa.UniqueConstraint("reference", name=op.f("uq_government_loads_reference")),
    )
    op.create_index(
        op.f("ix_government_loads_delivery_order_id"),
        "government_loads",
        ["delivery_order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_government_loads_status"), "government_loads", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_government_loads_status"), table_name="government_loads")
    op.drop_index(op.f("ix_government_loads_delivery_order_id"), table_name="government_loads")
    op.drop_table("government_loads")
    op.drop_index(op.f("ix_delivery_orders_allocation_id"), table_name="delivery_orders")
    op.drop_table("delivery_orders")
    op.drop_index(op.f("ix_allocations_agency_id"), table_name="allocations")
    op.drop_table("allocations")
    op.drop_table("reference_counters")
    op.drop_table("government_agencies")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
