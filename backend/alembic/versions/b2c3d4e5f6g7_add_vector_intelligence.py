"""Add vector intelligence tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2024-12-01

This migration adds:
- pgvector extension for embeddings
- Embedding columns on claims
- Entity knowledge base for learning
- Source credibility tracking
- Narrative clusters for trend detection
- Verification corrections for feedback learning
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (Neon supports this)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Add embedding column to claims table
    # Using 1536 dimensions for OpenAI text-embedding-3-small
    op.execute('ALTER TABLE claims ADD COLUMN IF NOT EXISTS embedding vector(1536)')
    
    # Create index for similarity search (IVFFlat for performance)
    op.execute('''
        CREATE INDEX IF NOT EXISTS claims_embedding_idx 
        ON claims USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    ''')
    
    # Entity Knowledge Base - stores verified facts about entities
    op.create_table(
        'entity_knowledge',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('entity_id', sa.Integer(), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fact_text', sa.Text(), nullable=False),
        sa.Column('fact_type', sa.String(50)),  # "position", "statement", "action", "relationship"
        sa.Column('confidence', sa.Float(), default=0.5),
        sa.Column('source_claim_id', sa.String(), sa.ForeignKey('claims.id', ondelete='SET NULL')),
        sa.Column('verified_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),  # For time-sensitive facts
        sa.Column('contradicted_by', ARRAY(sa.String())),  # Claim IDs that contradict this
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add embedding column to entity_knowledge
    op.execute('ALTER TABLE entity_knowledge ADD COLUMN fact_embedding vector(1536)')
    
    # Unique constraint on entity + fact combination
    op.create_index(
        'ix_entity_knowledge_unique_fact',
        'entity_knowledge',
        ['entity_id', 'fact_text'],
        unique=True
    )
    
    # Source Credibility Tracking
    op.create_table(
        'source_credibility',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_domain', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('source_name', sa.String(255)),  # Human-readable name
        sa.Column('source_type', sa.String(50)),  # "news", "government", "social", "satire"
        sa.Column('total_claims', sa.Integer(), default=0),
        sa.Column('verified_count', sa.Integer(), default=0),
        sa.Column('debunked_count', sa.Integer(), default=0),
        sa.Column('misleading_count', sa.Integer(), default=0),
        sa.Column('credibility_score', sa.Float(), default=0.5),  # 0.0 to 1.0
        sa.Column('bias_indicators', JSONB),  # {"political_lean": "left/center/right", "sensationalism": 0.0-1.0}
        sa.Column('is_whitelisted', sa.Boolean(), default=False),
        sa.Column('is_blacklisted', sa.Boolean(), default=False),
        sa.Column('last_claim_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Narrative Clusters - for tracking misinformation campaigns
    op.create_table(
        'narrative_clusters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cluster_name', sa.String(255)),
        sa.Column('description', sa.Text()),
        sa.Column('claim_ids', ARRAY(sa.String())),  # Claims in this cluster
        sa.Column('primary_topics', ARRAY(sa.Integer())),  # Topic IDs
        sa.Column('primary_entities', ARRAY(sa.Integer())),  # Entity IDs
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_seen', sa.DateTime()),
        sa.Column('claim_count', sa.Integer(), default=0),
        sa.Column('spread_velocity', sa.Float()),  # Claims per hour
        sa.Column('debunked_ratio', sa.Float()),  # Ratio of debunked claims
        sa.Column('risk_score', sa.Float()),  # 0.0 to 1.0
        sa.Column('is_coordinated', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('primary_sources', ARRAY(sa.String())),  # Domains spreading this
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add centroid embedding for narrative clusters
    op.execute('ALTER TABLE narrative_clusters ADD COLUMN centroid_embedding vector(1536)')
    
    # Verification Corrections - for learning from human feedback
    op.create_table(
        'verification_corrections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('claim_id', sa.String(), sa.ForeignKey('claims.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_status', sa.String(50), nullable=False),
        sa.Column('corrected_status', sa.String(50), nullable=False),
        sa.Column('correction_reason', sa.Text()),
        sa.Column('corrector_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('corrector_type', sa.String(50)),  # "internal", "user", "expert", "partner"
        sa.Column('confidence_delta', sa.Float()),  # How much confidence changed
        sa.Column('evidence_provided', ARRAY(sa.String())),  # URLs provided as evidence
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Index for analytics on corrections
    op.create_index(
        'ix_verification_corrections_status',
        'verification_corrections',
        ['original_status', 'corrected_status']
    )
    
    # Claim-Entity junction table (many-to-many)
    op.create_table(
        'claim_entities',
        sa.Column('claim_id', sa.String(), sa.ForeignKey('claims.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('entity_id', sa.Integer(), sa.ForeignKey('entities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('mention_type', sa.String(50)),  # "subject", "object", "mentioned"
        sa.Column('sentiment', sa.Float()),  # -1.0 to 1.0
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    
    # Add metadata columns to claims for AI analysis
    op.add_column('claims', sa.Column('ai_confidence', sa.Float()))
    op.add_column('claims', sa.Column('processing_metadata', JSONB))  # Store agent results
    op.add_column('claims', sa.Column('narrative_cluster_id', sa.Integer(), sa.ForeignKey('narrative_clusters.id')))
    
    # Add extra data to entities
    op.add_column('entities', sa.Column('aliases', ARRAY(sa.String())))  # Alternative names
    op.add_column('entities', sa.Column('political_affiliation', sa.String(100)))
    op.add_column('entities', sa.Column('position', sa.String(255)))  # Current position
    op.add_column('entities', sa.Column('claim_count', sa.Integer(), default=0))


def downgrade() -> None:
    # Remove new columns from entities
    op.drop_column('entities', 'claim_count')
    op.drop_column('entities', 'position')
    op.drop_column('entities', 'political_affiliation')
    op.drop_column('entities', 'aliases')
    
    # Remove new columns from claims
    op.drop_column('claims', 'narrative_cluster_id')
    op.drop_column('claims', 'processing_metadata')
    op.drop_column('claims', 'ai_confidence')
    
    # Drop new tables
    op.drop_table('claim_entities')
    op.drop_table('verification_corrections')
    op.drop_table('narrative_clusters')
    op.drop_table('source_credibility')
    op.drop_table('entity_knowledge')
    
    # Drop embedding columns and indexes
    op.execute('DROP INDEX IF EXISTS claims_embedding_idx')
    op.execute('ALTER TABLE claims DROP COLUMN IF EXISTS embedding')
    
    # Note: We don't drop pgvector extension as other things might depend on it

