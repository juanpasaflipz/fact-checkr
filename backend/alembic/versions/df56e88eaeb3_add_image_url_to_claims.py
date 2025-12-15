"""add image_url to claims

Revision ID: df56e88eaeb3
Revises: fb09f6977e8a
Create Date: 2025-12-15 16:12:06.678661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df56e88eaeb3'
down_revision: Union[str, Sequence[str], None] = 'fb09f6977e8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('claims', sa.Column('image_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('claims', 'image_url')
