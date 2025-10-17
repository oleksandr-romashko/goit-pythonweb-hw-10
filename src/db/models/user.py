"""User ORM model."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums.user_roles import UserRole
from .mixins import TimestampMixin

# Used for type hints only; avoids circular imports at runtime
if TYPE_CHECKING:
    from .contact import Contact


class User(TimestampMixin, Base):
    """ORM model representing an application user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(), nullable=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        String(20), nullable=False, default=UserRole.USER, server_default=UserRole.USER
    )

    contacts: Mapped[List["Contact"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"
