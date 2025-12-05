"""Add market tier restrictions

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2025-01-20 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h8i9j0k1l2m3'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add market tier restrictions and related tables."""
    # Add created_by_user_id to markets table
    op.add_column('markets', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_market_creator',
        'markets',
        'users',
        ['created_by_user_id'],
        ['id']
    )
    
    # Create market_proposals table
    op.create_table(
        'market_proposals',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('resolution_criteria', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),  # pending, approved, rejected
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_proposal_user'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name='fk_proposal_reviewer')
    )
    op.create_index('idx_market_proposals_user', 'market_proposals', ['user_id'])
    op.create_index('idx_market_proposals_status', 'market_proposals', ['status'])
    
    # Create user_market_stats table
    op.create_table(
        'user_market_stats',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_volume', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_credits_earned', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_stats_user')
    )
    
    # Create market_notifications table
    op.create_table(
        'market_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(), nullable=False),  # probability_change, resolution, new_market
        sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notification_user'),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], name='fk_notification_market')
    )
    op.create_index('idx_market_notifications_user', 'market_notifications', ['user_id', 'read'])
    op.create_index('idx_market_notifications_market', 'market_notifications', ['market_id'])


def downgrade() -> None:
    """Remove market tier restrictions."""
    op.drop_index('idx_market_notifications_market', 'market_notifications')
    op.drop_index('idx_market_notifications_user', 'market_notifications')
    op.drop_table('market_notifications')
    op.drop_table('user_market_stats')
    op.drop_index('idx_market_proposals_status', 'market_proposals')
    op.drop_index('idx_market_proposals_user', 'market_proposals')
    op.drop_table('market_proposals')
    op.drop_constraint('fk_market_creator', 'markets', type_='foreignkey')
    op.drop_column('markets', 'created_by_user_id')

