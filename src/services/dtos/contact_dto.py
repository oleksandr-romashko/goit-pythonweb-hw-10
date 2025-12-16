"""DTO module representing contact"""

from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, Self

from src.db.models import Contact


@dataclass(slots=True, frozen=True)
class ContactDTO:
    """DTO representing contact information"""

    id: int
    user_id: int

    first_name: str
    last_name: str
    email: str
    phone_number: str
    birthdate: date
    info: str

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __str__(self) -> str:
        return (
            f"ContactDTO(id={self.id}, user_id={self.user_id}, "
            f"name={self.first_name} {self.last_name})"
        )

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_orm(cls, contact: Contact) -> Self:
        """Create DTO from ORM model."""
        return cls(
            id=contact.id,
            user_id=contact.user_id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone_number=contact.phone_number,
            birthdate=contact.birthdate,
            info=contact.info,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create DTO from dictionary (e.g. cache)."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone_number=data["phone_number"],
            birthdate=date.fromisoformat(data["birthdate"]),
            info=data.get("info", ""),
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

        # dates → isoformat
        data["birthdate"] = self.birthdate.isoformat()

        if data["created_at"]:
            data["created_at"] = data["created_at"].isoformat()
        if data["updated_at"]:
            data["updated_at"] = data["updated_at"].isoformat()

        return data
