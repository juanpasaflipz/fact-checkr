"""Add reading_level column to claims

Revision ID: l1m2n3o4p5
Revises: k1l2m3n4o5p6
Create Date: 2025-12-08 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "l1m2n3o4p5"
# Chain after the latest existing head to avoid multiple heads
down_revision: Union[str, None] = "add_evidence_details"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reading_level column if missing (idempotent)."""
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='claims' AND column_name='reading_level'"
        )
    ).fetchone()
    if not exists:
        op.add_column(
            "claims",
            sa.Column("reading_level", sa.String(), nullable=True, server_default="normal"),
        )
        # Drop the server_default to avoid future inserts auto-filling if application sets it
        op.alter_column("claims", "reading_level", server_default=None)


def downgrade() -> None:
    """Remove reading_level column."""
    op.drop_column("claims", "reading_level")

