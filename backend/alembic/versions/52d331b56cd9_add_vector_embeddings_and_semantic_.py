"""add_vector_embeddings_and_semantic_search

Revision ID: 52d331b56cd9
Revises: j0k1l2m3n4o5
Create Date: 2025-12-06 18:28:05.423475

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '52d331b56cd9'
down_revision: Union[str, Sequence[str], None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vector embeddings and semantic search capabilities."""

    # Enable pgvector extension (will work on Neon, may fail locally)
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        vector_available = True
    except Exception:
        # pgvector not available (e.g., local PostgreSQL without extension)
        vector_available = False

    if vector_available:
        # Add embedding column to claims table for semantic search (if not exists)
        from sqlalchemy import inspect
        conn = op.get_bind()
        inspector = inspect(conn)
        claims_columns = [col['name'] for col in inspector.get_columns('claims')]
        entities_columns = [col['name'] for col in inspector.get_columns('entities')]
        
        if 'embedding' not in claims_columns:
            op.add_column('claims',
                sa.Column('embedding', Vector(1536), nullable=True)
            )

        # Add embedding column to entities table for entity similarity (if not exists)
        if 'embedding' not in entities_columns:
            op.add_column('entities',
                sa.Column('embedding', Vector(1536), nullable=True)
            )

        # Create indexes for vector similarity search (if not exists)
        from sqlalchemy import inspect
        conn = op.get_bind()
        inspector = inspect(conn)
        claims_indexes = [idx['name'] for idx in inspector.get_indexes('claims')]
        entities_indexes = [idx['name'] for idx in inspector.get_indexes('entities')]
        
        if 'claims_embedding_idx' not in claims_indexes:
            op.create_index('claims_embedding_idx', 'claims', ['embedding'],
                postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})
        if 'entities_embedding_idx' not in entities_indexes:
            op.create_index('entities_embedding_idx', 'entities', ['embedding'],
                postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'})
    else:
        # Fallback: use JSONB to store embeddings as arrays when pgvector is not available
        from sqlalchemy import inspect
        conn = op.get_bind()
        inspector = inspect(conn)
        claims_columns = [col['name'] for col in inspector.get_columns('claims')]
        entities_columns = [col['name'] for col in inspector.get_columns('entities')]
        
        if 'embedding' not in claims_columns:
            op.add_column('claims',
                sa.Column('embedding', sa.JSON(), nullable=True)
            )
        if 'embedding' not in entities_columns:
            op.add_column('entities',
                sa.Column('embedding', sa.JSON(), nullable=True)
            )
        # Note: No vector indexes can be created without pgvector

    # Create table for embedding metadata and versioning
    op.create_table(
        'embedding_metadata',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('table_name', sa.String(50), nullable=False),  # 'claims' or 'entities'
        sa.Column('record_id', sa.String(), nullable=False),  # claim.id or entity.id
        sa.Column('model_version', sa.String(50), nullable=False, default='text-embedding-3-small'),
        sa.Column('embedding_version', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('table_name', 'record_id', name='unique_table_record')
    )

    # Create indexes for metadata table
    op.create_index('embedding_metadata_table_record_idx', 'embedding_metadata', ['table_name', 'record_id'])
    op.create_index('embedding_metadata_created_idx', 'embedding_metadata', ['created_at'])


def downgrade() -> None:
    """Remove vector embeddings and semantic search capabilities."""

    # Drop embedding metadata table
    op.drop_index('embedding_metadata_created_idx', table_name='embedding_metadata')
    op.drop_index('embedding_metadata_table_record_idx', table_name='embedding_metadata')
    op.drop_table('embedding_metadata')

    # Drop vector indexes (only if they exist)
    try:
        op.drop_index('entities_embedding_idx', table_name='entities')
    except Exception:
        pass  # Index might not exist if pgvector wasn't available

    try:
        op.drop_index('claims_embedding_idx', table_name='claims')
    except Exception:
        pass  # Index might not exist if pgvector wasn't available

    # Drop embedding columns
    op.drop_column('entities', 'embedding')
    op.drop_column('claims', 'embedding')

    # Note: We don't drop the vector extension as other tables might still use it
