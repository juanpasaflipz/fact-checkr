"""Add verification enhancements: confidence, evidence strength, review queue

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2025-01-20 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enhanced verification fields to claims table."""
    # Add confidence score
    op.add_column('claims', sa.Column('confidence', sa.Float(), nullable=True))
    
    # Add evidence strength
    op.add_column('claims', sa.Column('evidence_strength', sa.String(), nullable=True))
    
    # Add key evidence points (JSON array)
    op.add_column('claims', sa.Column('key_evidence_points', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # Add review queue fields
    op.add_column('claims', sa.Column('needs_review', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('claims', sa.Column('review_priority', sa.String(), nullable=True))
    
    # Add agent findings (for multi-agent system)
    op.add_column('claims', sa.Column('agent_findings', postgresql.JSON(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove enhanced verification fields."""
    op.drop_column('claims', 'agent_findings')
    op.drop_column('claims', 'review_priority')
    op.drop_column('claims', 'needs_review')
    op.drop_column('claims', 'key_evidence_points')
    op.drop_column('claims', 'evidence_strength')
    op.drop_column('claims', 'confidence')

