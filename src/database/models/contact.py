"""Contact ORM model."""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import TimestampMixin

# Used for type hints only; avoids circular imports at runtime
if TYPE_CHECKING:
    from .auth import User


class Contact(TimestampMixin, Base):
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

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="contacts")

    def __repr__(self) -> str:
        return f"Contact(id={self.id!r}, owner_id={self.user_id!r})"
