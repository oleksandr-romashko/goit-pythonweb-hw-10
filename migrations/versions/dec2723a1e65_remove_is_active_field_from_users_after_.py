"""Remove is_active field from users after migration

Revision ID: dec2723a1e65
Revises: 11a8e77b2534
Create Date: 2025-10-13 11:50:55.886553

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dec2723a1e65"
down_revision: Union[str, Sequence[str], None] = "11a8e77b2534"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore server default to True."""
    op.alter_column(
        "users",
        "is_active",
        server_default=None,
    )


def downgrade() -> None:
    """Restore server default to True."""
    op.alter_column(
        "users",
        "is_active",
        server_default=sa.true(),
    )
