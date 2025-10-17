"""Fix entities timestamps generation in db

Revision ID: 92e907d3c909
Revises: 186f90aef183
Create Date: 2025-10-12 00:45:28.752100

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "92e907d3c909"
down_revision: Union[str, Sequence[str], None] = "186f90aef183"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to set DB-side default timestamps."""
    # Users table
    op.alter_column(
        "users",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "users",
        "updated_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
    )

    # Contacts table
    op.alter_column(
        "contacts",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "contacts",
        "updated_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema to revert DB-side default timestamps."""
    op.alter_column(
        "users",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "users",
        "updated_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "contacts",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "contacts",
        "updated_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
    )
