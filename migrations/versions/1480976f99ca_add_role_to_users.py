"""Add role to users

Revision ID: 1480976f99ca
Revises: dec2723a1e65
Create Date: 2025-10-13 14:04:42.867992

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1480976f99ca"
down_revision: Union[str, Sequence[str], None] = "dec2723a1e65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
