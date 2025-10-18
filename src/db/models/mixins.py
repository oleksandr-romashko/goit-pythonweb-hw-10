"""Common reusable mixins for ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at and updated_at timestamp fields, set on the DB server."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()  # pylint: disable=E1102
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=E1102
        onupdate=func.now(),  # pylint: disable=E1102
    )
