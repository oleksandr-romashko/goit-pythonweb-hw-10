"""DTO module representing user"""

from dataclasses import dataclass, asdict
from datetime import datetime
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
    is_email_confirmed: bool
    avatar: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

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
            is_email_confirmed=user.is_email_confirmed,
            avatar=getattr(user, "avatar", None),
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "UserDTO":
        """Create DTO from dictionary (e.g. cache)."""
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            hashed_password=data["hashed_password"],
            role=UserRole(data["role"]),  # str -> Enum
            is_active=data["is_active"],
            is_email_confirmed=data["is_email_confirmed"],
            avatar=data.get("avatar"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
        )

    def to_dict(self) -> dict:
        """Convert DTO to dictionary for JSON / cache serialization."""
        data = asdict(self)
        data["role"] = self.role.value if isinstance(self.role, UserRole) else self.role
        if data["created_at"]:
            data["created_at"] = data["created_at"].isoformat()
        if data["updated_at"]:
            data["updated_at"] = data["updated_at"].isoformat()
        return data
