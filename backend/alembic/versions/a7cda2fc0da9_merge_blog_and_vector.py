"""merge_blog_and_vector

Revision ID: a7cda2fc0da9
Revises: 52d331b56cd9, k1l2m3n4o5p6
Create Date: 2025-12-07 19:01:37.367386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7cda2fc0da9'
down_revision: Union[str, Sequence[str], None] = ('52d331b56cd9', 'k1l2m3n4o5p6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
