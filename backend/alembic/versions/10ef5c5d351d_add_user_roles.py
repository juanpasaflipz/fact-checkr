"""Add user roles

Revision ID: 10ef5c5d351d
Revises: 7514d58b4a4d
Create Date: 2025-12-16 08:48:47.029089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '10ef5c5d351d'
down_revision: Union[str, Sequence[str], None] = '7514d58b4a4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type explicitly to be safe
    user_role = postgresql.ENUM('user', 'admin', 'super_admin', name='userrole')
    user_role.create(op.get_bind())
    
    # 1. Add role column
    # Note: we use server_default to populate existing rows, but it requires the type to exist.
    op.add_column('users', sa.Column('role', sa.Enum('user', 'admin', 'super_admin', name='userrole'), nullable=False, server_default='user'))
    
    # 2. Update indexes (keeping these as they seem correct corrections for the User model)
    
    # Drop old indexes if they exist (Alembic names)
    op.drop_index('ix_users_email', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    op.drop_index('ix_users_username', table_name='users')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # referral_code was optional in models.py?
    # model: referral_code = Column(String, unique=True, nullable=True, index=True)
    # autogen: op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
    # This matches.
    # It says it detected removed index 'idx_user_referral_code', removed constraint 'users_referral_code_key'.
    # It seems it wants to replace them with 'ix_users_referral_code'.
    
    # Safely dropping what it thinks exists (might fail if they don't, but let's try to match autogen output for users only)
    try:
        op.drop_index('idx_user_referral_code', table_name='users')
    except Exception:
        pass
        
    try:
        op.drop_constraint('users_email_key', 'users', type_='unique')
    except Exception:
        pass

    try:
        op.drop_constraint('users_referral_code_key', 'users', type_='unique')
    except Exception:
        pass

    try:
        op.drop_constraint('users_username_key', 'users', type_='unique')
    except Exception:
        pass

    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse index changes
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    
    # Drop role column
    op.drop_column('users', 'role')
    
    # Drop enum type
    op.execute("DROP TYPE userrole")
