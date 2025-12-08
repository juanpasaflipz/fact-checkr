"""add evidence_details to claims

Revision ID: add_evidence_details
Revises: k1l2m3n4o5p6
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_evidence_details'
down_revision: Union[str, None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add evidence_details JSON column to claims table"""
    op.add_column('claims', sa.Column('evidence_details', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove evidence_details column from claims table"""
    op.drop_column('claims', 'evidence_details')

