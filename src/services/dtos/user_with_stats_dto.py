"""DTO module representing user with additional stats"""

from dataclasses import dataclass
from datetime import datetime
from typing import Self, Optional, Dict

from src.db.models.enums.user_roles import UserRole
from src.db.models.user import User


@dataclass(slots=True, frozen=True)
class UserWithStatsDTO:
    """DTO representing a user along with statistics such as contacts count."""

    id: int
    username: str
    email: Optional[str]
    role: UserRole
    is_active: Optional[bool]
    avatar: Optional[str]
    contacts_count: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_orm_with_count(
        cls,
        user: User,
        contacts_count: Optional[int] = None,
        hide_email: bool = False,
        hide_personal: bool = False,
    ) -> Self:
        """Create DTO from ORM user and contacts count."""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email if not hide_email else None,
            role=user.role,
            is_active=user.is_active if not hide_personal else None,
            avatar=user.avatar,
            created_at=user.created_at if not hide_personal else None,
            updated_at=user.updated_at if not hide_personal else None,
            contacts_count=contacts_count if not hide_personal else None,
        )

    def to_dict(self) -> Dict:
        """Convert DTO object into a dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "is_active": self.is_active,
            "avatar": self.avatar,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "contacts_count": self.contacts_count,
        }
