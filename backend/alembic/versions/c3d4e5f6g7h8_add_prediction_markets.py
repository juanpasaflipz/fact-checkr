"""Add prediction markets module

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-01-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create MarketStatus enum
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE marketstatus AS ENUM ('open', 'resolved', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))
    
    # Create markets table
    op.create_table('markets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('claim_id', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('open', 'resolved', 'cancelled', name='marketstatus', create_type=False), nullable=False, server_default='open'),
        sa.Column('yes_liquidity', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('no_liquidity', sa.Float(), nullable=False, server_default='1000.0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('closes_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('winning_outcome', sa.String(), nullable=True),
        sa.Column('resolution_source', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_markets_slug'), 'markets', ['slug'], unique=True)
    op.create_index(op.f('ix_markets_claim_id'), 'markets', ['claim_id'], unique=False)
    
    # Create user_balances table
    op.create_table('user_balances',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('available_credits', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('locked_credits', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create market_trades table
    op.create_table('market_trades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('outcome', sa.String(), nullable=False),
        sa.Column('shares', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_trades_market_id'), 'market_trades', ['market_id'], unique=False)
    op.create_index(op.f('ix_market_trades_user_id'), 'market_trades', ['user_id'], unique=False)
    op.create_index(op.f('ix_market_trades_created_at'), 'market_trades', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_market_trades_created_at'), table_name='market_trades')
    op.drop_index(op.f('ix_market_trades_user_id'), table_name='market_trades')
    op.drop_index(op.f('ix_market_trades_market_id'), table_name='market_trades')
    op.drop_table('market_trades')
    
    op.drop_table('user_balances')
    
    op.drop_index(op.f('ix_markets_claim_id'), table_name='markets')
    op.drop_index(op.f('ix_markets_slug'), table_name='markets')
    op.drop_table('markets')
    
    op.drop_column('users', 'is_admin')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS marketstatus")

