"""Add referral system

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2025-01-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import secrets

# revision identifiers, used by Alembic.
revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add referral tracking to users and create referral_bonuses table."""
    # Add referral fields to users table
    op.add_column('users', sa.Column('referred_by_user_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('referral_code', sa.String(), nullable=True, unique=True))
    op.create_foreign_key(
        'fk_user_referred_by',
        'users',
        'users',
        ['referred_by_user_id'],
        ['id']
    )
    op.create_index('idx_user_referral_code', 'users', ['referral_code'])
    
    # Create referral_bonuses table
    op.create_table(
        'referral_bonuses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('referrer_id', sa.Integer(), nullable=False),
        sa.Column('referred_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('bonus_credits', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id'], name='fk_referral_referrer'),
        sa.ForeignKeyConstraint(['referred_id'], ['users.id'], name='fk_referral_referred')
    )
    op.create_index('idx_referral_referrer', 'referral_bonuses', ['referrer_id'])
    op.create_index('idx_referral_paid', 'referral_bonuses', ['paid'])


def downgrade() -> None:
    """Remove referral system."""
    op.drop_index('idx_referral_paid', 'referral_bonuses')
    op.drop_index('idx_referral_referrer', 'referral_bonuses')
    op.drop_table('referral_bonuses')
    op.drop_index('idx_user_referral_code', 'users')
    op.drop_constraint('fk_user_referred_by', 'users', type_='foreignkey')
    op.drop_column('users', 'referral_code')
    op.drop_column('users', 'referred_by_user_id')

