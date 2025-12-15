"""Add WhatsApp tables, Verdict and Evidence

Revision ID: fb09f6977e8a
Revises: 7fecb6e4b649
Create Date: 2025-12-15 10:45:06.032892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fb09f6977e8a'
down_revision: Union[str, Sequence[str], None] = '7fecb6e4b649'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create whatsapp_users table
    op.create_table('whatsapp_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('phone_hash', sa.String(), nullable=False),
        sa.Column('locale', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_users_phone_hash'), 'whatsapp_users', ['phone_hash'], unique=True)

    # Create whatsapp_messages table
    op.create_table('whatsapp_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('wa_message_id', sa.String(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['whatsapp_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_messages_status'), 'whatsapp_messages', ['status'], unique=False)
    op.create_index(op.f('ix_whatsapp_messages_user_id'), 'whatsapp_messages', ['user_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_messages_wa_message_id'), 'whatsapp_messages', ['wa_message_id'], unique=True)

    # Create verdicts table
    op.create_table('verdicts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.String(), nullable=False),
        sa.Column('label', postgresql.ENUM('VERIFIED', 'MOSTLY_TRUE', 'MIXED', 'MOSTLY_FALSE', 'DEBUNKED', 'UNVERIFIED', 'MISLEADING', name='verificationstatus', create_type=False), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('explanation_short', sa.JSON(), nullable=True),
        sa.Column('explanation_long', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id')
    )

    # Create evidence table
    op.create_table('evidence',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('claim_id', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('outlet', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('quote', sa.Text(), nullable=True),
        sa.Column('stance', sa.String(), nullable=True),
        sa.Column('reliability', sa.String(), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_claim_id'), 'evidence', ['claim_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('evidence')
    op.drop_table('verdicts')
    op.drop_table('whatsapp_messages')
    op.drop_table('whatsapp_users')

