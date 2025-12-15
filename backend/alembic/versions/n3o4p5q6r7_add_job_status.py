"""add_job_status

Revision ID: n3o4p5q6r7
Revises: m2n3o4p5q6
Create Date: 2025-12-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'n3o4p5q6r7'
down_revision = 'm2n3o4p5q6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('job_status',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_status_job_type'), 'job_status', ['job_type'], unique=False)
    op.create_index(op.f('ix_job_status_status'), 'job_status', ['status'], unique=False)
    op.create_index(op.f('ix_job_status_created_at'), 'job_status', ['created_at'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_job_status_created_at'), table_name='job_status')
    op.drop_index(op.f('ix_job_status_status'), table_name='job_status')
    op.drop_index(op.f('ix_job_status_job_type'), table_name='job_status')
    op.drop_table('job_status')
