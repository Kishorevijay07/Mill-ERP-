"""add document content column

Revision ID: 5f27da3e5ef0
Revises: 8d1b29884ce2
Create Date: 2026-09-19 15:47:03.186540+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f27da3e5ef0"
down_revision: str | None = "8d1b29884ce2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("content", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "content")
