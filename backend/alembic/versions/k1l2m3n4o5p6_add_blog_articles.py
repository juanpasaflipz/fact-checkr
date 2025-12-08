"""Add blog articles table

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2025-01-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add blog articles table for AI-generated content."""
    
    # Create blog_articles table first
    op.create_table(
        'blog_articles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), unique=True, nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('article_type', sa.String(), nullable=False),
        sa.Column('edition_number', sa.Integer(), nullable=True),
        sa.Column('data_context', postgresql.JSONB(), nullable=True),
        sa.Column('published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('telegraph_url', sa.String(), nullable=True),
        sa.Column('telegraph_path', sa.String(), nullable=True),
        sa.Column('twitter_posted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('twitter_url', sa.String(), nullable=True),
        sa.Column('video_generated', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('youtube_url', sa.String(), nullable=True),
        sa.Column('tiktok_video_path', sa.String(), nullable=True),
        sa.Column('topic_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name='fk_blog_articles_topic')
    )
    
    # Create indexes
    op.create_index('idx_blog_articles_slug', 'blog_articles', ['slug'])
    op.create_index('idx_blog_articles_published', 'blog_articles', ['published', 'published_at'])
    op.create_index('idx_blog_articles_type', 'blog_articles', ['article_type', 'edition_number'])
    op.create_index('idx_blog_articles_topic', 'blog_articles', ['topic_id'])
    
    # Create blog_article_claims association table (after blog_articles exists)
    op.create_table(
        'blog_article_claims',
        sa.Column('blog_article_id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('blog_article_id', 'claim_id'),
        sa.ForeignKeyConstraint(['blog_article_id'], ['blog_articles.id'], name='fk_blog_article_claims_article'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], name='fk_blog_article_claims_claim')
    )
    op.create_index('idx_blog_article_claims_article', 'blog_article_claims', ['blog_article_id'])
    op.create_index('idx_blog_article_claims_claim', 'blog_article_claims', ['claim_id'])


def downgrade() -> None:
    """Remove blog articles table."""
    op.drop_index('idx_blog_articles_topic', 'blog_articles')
    op.drop_index('idx_blog_articles_type', 'blog_articles')
    op.drop_index('idx_blog_articles_published', 'blog_articles')
    op.drop_index('idx_blog_articles_slug', 'blog_articles')
    op.drop_table('blog_articles')
    
    op.drop_index('idx_blog_article_claims_claim', 'blog_article_claims')
    op.drop_index('idx_blog_article_claims_article', 'blog_article_claims')
    op.drop_table('blog_article_claims')

