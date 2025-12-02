"""Add market categories and resolution criteria

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-01-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add category and resolution_criteria fields to markets table."""
    # Add category field (for filtering by Mexican system-level issues)
    op.add_column('markets', sa.Column('category', sa.String(), nullable=True))
    
    # Add resolution_criteria field (for transparent resolution rules)
    op.add_column('markets', sa.Column('resolution_criteria', sa.Text(), nullable=True))
    
    # Create index on category for faster filtering
    op.create_index(op.f('ix_markets_category'), 'markets', ['category'], unique=False)


def downgrade() -> None:
    """Remove category and resolution_criteria fields."""
    op.drop_index(op.f('ix_markets_category'), table_name='markets')
    op.drop_column('markets', 'resolution_criteria')
    op.drop_column('markets', 'category')

