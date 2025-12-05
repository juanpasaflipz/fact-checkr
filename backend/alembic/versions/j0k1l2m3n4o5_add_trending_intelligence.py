"""Add trending intelligence tables

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2025-01-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trending intelligence tables for hybrid topic detection."""
    
    # Create trending_topics table
    op.create_table(
        'trending_topics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_name', sa.String(255), nullable=False),
        sa.Column('topic_keywords', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=False),
        sa.Column('engagement_velocity', sa.Float(), nullable=True),
        sa.Column('cross_platform_correlation', sa.Float(), nullable=True),
        sa.Column('context_relevance_score', sa.Float(), nullable=True),
        sa.Column('misinformation_risk_score', sa.Float(), nullable=True),
        sa.Column('final_priority_score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('topic_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_trending_topics_score', 'trending_topics', ['final_priority_score'])
    op.create_index('idx_trending_topics_detected', 'trending_topics', ['detected_at'])
    op.create_index('idx_trending_topics_status', 'trending_topics', ['status'])
    
    # Create trending_topic_sources association table
    op.create_table(
        'trending_topic_sources',
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('topic_id', 'source_id'),
        sa.ForeignKeyConstraint(['topic_id'], ['trending_topics.id'], name='fk_topic_sources_topic'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], name='fk_topic_sources_source')
    )
    op.create_index('idx_topic_sources_topic', 'trending_topic_sources', ['topic_id'])
    op.create_index('idx_topic_sources_source', 'trending_topic_sources', ['source_id'])
    
    # Create context_intelligence table
    op.create_table(
        'context_intelligence',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_key', sa.String(255), unique=True, nullable=False),
        sa.Column('political_context', postgresql.JSONB(), nullable=True),
        sa.Column('economic_context', postgresql.JSONB(), nullable=True),
        sa.Column('social_context', postgresql.JSONB(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('noise_filter_score', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_context_topic_key', 'context_intelligence', ['topic_key'])
    
    # Create topic_priority_queue table
    op.create_table(
        'topic_priority_queue',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('priority_score', sa.Float(), nullable=False),
        sa.Column('queued_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_status', sa.String(20), server_default='pending'),
        sa.ForeignKeyConstraint(['topic_id'], ['trending_topics.id'], name='fk_priority_queue_topic')
    )
    op.create_index('idx_priority_queue_score', 'topic_priority_queue', ['priority_score', 'queued_at'])
    op.create_index('idx_priority_queue_status', 'topic_priority_queue', ['processing_status'])
    
    # Add trending_topic_id to sources table
    op.add_column('sources', sa.Column('trending_topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_sources_trending_topic',
        'sources',
        'trending_topics',
        ['trending_topic_id'],
        ['id']
    )
    op.create_index('idx_sources_trending_topic', 'sources', ['trending_topic_id'])


def downgrade() -> None:
    """Remove trending intelligence tables."""
    op.drop_index('idx_sources_trending_topic', 'sources')
    op.drop_constraint('fk_sources_trending_topic', 'sources', type_='foreignkey')
    op.drop_column('sources', 'trending_topic_id')
    
    op.drop_index('idx_priority_queue_status', 'topic_priority_queue')
    op.drop_index('idx_priority_queue_score', 'topic_priority_queue')
    op.drop_table('topic_priority_queue')
    
    op.drop_index('idx_context_topic_key', 'context_intelligence')
    op.drop_table('context_intelligence')
    
    op.drop_index('idx_topic_sources_source', 'trending_topic_sources')
    op.drop_index('idx_topic_sources_topic', 'trending_topic_sources')
    op.drop_table('trending_topic_sources')
    
    op.drop_index('idx_trending_topics_status', 'trending_topics')
    op.drop_index('idx_trending_topics_detected', 'trending_topics')
    op.drop_index('idx_trending_topics_score', 'trending_topics')
    op.drop_table('trending_topics')

