"""Add user preferences for market categories

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-01-20 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user preferences for market categories."""
    # Add preferred_categories field (JSON array of category strings)
    op.add_column('users', sa.Column('preferred_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add onboarding_completed field
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Remove user preferences."""
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'preferred_categories')

