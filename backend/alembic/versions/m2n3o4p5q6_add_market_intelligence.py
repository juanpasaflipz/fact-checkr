"""Add market intelligence tables

Revision ID: m2n3o4p5q6
Revises: l1m2n3o4p5
Create Date: 2025-01-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'm2n3o4p5q6'
down_revision: Union[str, None] = 'l1m2n3o4p5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add market intelligence tables."""
    
    # Create market_prediction_factors table
    # Stores prediction outputs from the synthesizer agent
    op.create_table('market_prediction_factors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('analysis_tier', sa.Integer(), nullable=False, server_default='2'),
        
        # Probabilities
        sa.Column('raw_probability', sa.Float(), nullable=False),
        sa.Column('calibrated_probability', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        
        # Confidence interval
        sa.Column('probability_low', sa.Float(), nullable=True),
        sa.Column('probability_high', sa.Float(), nullable=True),
        
        # Factors (JSONB)
        sa.Column('key_factors', postgresql.JSONB(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('data_sources', postgresql.JSONB(), nullable=True),
        
        # Transparency
        sa.Column('reasoning_chain', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('data_freshness_hours', sa.Float(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mpf_market_time', 'market_prediction_factors', ['market_id', 'created_at'], unique=False)
    op.create_index('idx_mpf_agent_type', 'market_prediction_factors', ['agent_type'], unique=False)
    
    # Create agent_performance table
    # Tracks prediction accuracy for calibration
    op.create_table('agent_performance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.String(50), nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('predicted_probability', sa.Float(), nullable=False),
        sa.Column('actual_outcome', sa.String(10), nullable=True),  # 'yes', 'no', or NULL
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('prediction_date', sa.DateTime(), nullable=False),
        sa.Column('resolution_date', sa.DateTime(), nullable=True),
        
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Unique constraint: one prediction per agent per market
        sa.UniqueConstraint('agent_id', 'market_id', name='uq_agent_market_prediction')
    )
    op.create_index('idx_ap_agent', 'agent_performance', ['agent_id', 'prediction_date'], unique=False)
    op.create_index('idx_ap_market', 'agent_performance', ['market_id'], unique=False)
    
    # Create market_votes table
    # User votes on market outcomes (separate from trading)
    op.create_table('market_votes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('market_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('outcome', sa.String(10), nullable=False),  # 'yes' or 'no'
        sa.Column('confidence', sa.Integer(), nullable=True),  # 1-5
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        sa.ForeignKeyConstraint(['market_id'], ['markets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Each user can only vote once per market
        sa.UniqueConstraint('market_id', 'user_id', name='uq_market_user_vote'),
        # Confidence must be 1-5
        sa.CheckConstraint('confidence >= 1 AND confidence <= 5', name='ck_vote_confidence_range')
    )
    op.create_index('idx_mv_market', 'market_votes', ['market_id'], unique=False)
    op.create_index('idx_mv_user', 'market_votes', ['user_id'], unique=False)
    
    # Add question_embedding column to markets table for similarity search
    # Check if pgvector is available and add vector column
    conn = op.get_bind()
    try:
        # Check if vector extension exists
        result = conn.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result:
            op.add_column('markets', sa.Column('question_embedding', sa.LargeBinary(), nullable=True))
            # Use raw SQL to set the type since alembic doesn't support vector natively
            op.execute("ALTER TABLE markets ALTER COLUMN question_embedding TYPE vector(1536) USING question_embedding::vector(1536)")
    except Exception:
        # pgvector not available, skip vector column
        pass


def downgrade() -> None:
    """Remove market intelligence tables."""
    
    # Drop question_embedding from markets if it exists
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='markets' AND column_name='question_embedding'"
        )
    ).fetchone()
    if exists:
        op.drop_column('markets', 'question_embedding')
    
    # Drop tables
    op.drop_index('idx_mv_user', table_name='market_votes')
    op.drop_index('idx_mv_market', table_name='market_votes')
    op.drop_table('market_votes')
    
    op.drop_index('idx_ap_market', table_name='agent_performance')
    op.drop_index('idx_ap_agent', table_name='agent_performance')
    op.drop_table('agent_performance')
    
    op.drop_index('idx_mpf_agent_type', table_name='market_prediction_factors')
    op.drop_index('idx_mpf_market_time', table_name='market_prediction_factors')
    op.drop_table('market_prediction_factors')
