# =============================================================
# FILE: backend/alembic/versions/ae1850186102_add_user_default_address.py
# =============================================================

"""add_user_default_address

Revision ID: ae1850186102
Revises: d4c923cc9ba6
Create Date: 2026-11-23 18:32:13.056847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae1850186102'
down_revision: Union[str, Sequence[str], None] = 'd4c923cc9ba6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add default_address to users table."""
    op.add_column("users", sa.Column("default_address", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema: Remove default_address from users table."""
    op.drop_column("users", "default_address")