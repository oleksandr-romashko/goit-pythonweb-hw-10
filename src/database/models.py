"""Database Base ORM models."""

from datetime import datetime, date, timezone

from sqlalchemy import Integer, String, Text, DateTime, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Contact(Base):
    """ORM model representing a single contact entry."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=False)
    phone_number: Mapped[str] = mapped_column(String(40), nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    info: Mapped[str] = mapped_column(
        Text(), nullable=False, default="", server_default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
