"""Add enhanced source fields for Twitter Basic tier

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced data fields to sources table for Twitter Basic tier."""
    # Add JSON columns for enhanced data
    op.add_column('sources', sa.Column('engagement_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sources', sa.Column('author_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sources', sa.Column('media_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('sources', sa.Column('context_data', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add credibility score column
    op.add_column('sources', sa.Column('credibility_score', sa.Float(), nullable=True, server_default='0.5'))


def downgrade() -> None:
    """Remove enhanced data fields from sources table."""
    op.drop_column('sources', 'credibility_score')
    op.drop_column('sources', 'context_data')
    op.drop_column('sources', 'media_urls')
    op.drop_column('sources', 'author_metadata')
    op.drop_column('sources', 'engagement_metrics')

