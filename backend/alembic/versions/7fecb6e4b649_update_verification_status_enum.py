"""update_verification_status_enum

Revision ID: 7fecb6e4b649
Revises: n3o4p5q6r7
Create Date: 2025-12-15 10:36:10.296869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fecb6e4b649'
down_revision: Union[str, Sequence[str], None] = 'n3o4p5q6r7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new values to VerificationStatus enum
    # We must use autocommit block for ALTER TYPE ADD VALUE in Postgres
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE verificationstatus ADD VALUE IF NOT EXISTS 'Mostly True'")
        op.execute("ALTER TYPE verificationstatus ADD VALUE IF NOT EXISTS 'Mixed'")
        op.execute("ALTER TYPE verificationstatus ADD VALUE IF NOT EXISTS 'Mostly False'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres doesn't support removing values from Enums easily.
    # We typically leave them or would need to drop/recreate the type, which is destructive.
    pass
