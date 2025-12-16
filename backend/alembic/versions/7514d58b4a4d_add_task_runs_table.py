"""Add task_runs table

Revision ID: 7514d58b4a4d
Revises: df56e88eaeb3
Create Date: 2025-12-15 18:23:32.251944

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7514d58b4a4d'
down_revision: Union[str, Sequence[str], None] = 'df56e88eaeb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('task_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_type', sa.String(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_task_runs_dedup', 'task_runs', ['task_type', 'idempotency_key'], unique=True)


def downgrade():
    op.drop_index('idx_task_runs_dedup', table_name='task_runs')
    op.drop_table('task_runs')
