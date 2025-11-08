"""DTO module representing user"""

from dataclasses import dataclass
from typing import Optional, Self

from src.db.models import User
from src.db.models.enums import UserRole


@dataclass(slots=True, frozen=True)
class UserDTO:
    """DTO representing user information"""

    id: int
    username: str
    email: str
    hashed_password: str
    role: UserRole
    is_active: bool
    avatar: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"User(id={self.id}, username={self.username}, "
            f"role={self.role}, active={self.is_active})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_orm(cls, user: User) -> Self:
        """Create DTO from ORM model."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role,
            is_active=user.is_active,
            avatar=getattr(user, "avatar", None),
        )
