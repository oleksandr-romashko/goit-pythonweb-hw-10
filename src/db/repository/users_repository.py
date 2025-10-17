"""
Repository layer for User entities.

Provides asynchronous CRUD operations and query helpers.

This layer encapsulates all database logic, isolating it from business and routing layers.
"""

from typing import Optional, Any, List, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UsersRepository:
    """Repository for database operations with users"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_user(self, data: Dict[str, Any]) -> User:
        """Create a new user and persist it in the database."""
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> List[User]:
        """Return a paginated list of users."""
        stmt = (
            select(User).order_by(func.lower(User.username)).offset(skip).limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Return a single user by ID, or None if not found."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Return a single user by username, or None if not found."""
        stmt = select(User).where(User.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Return a single user by email, or None if not found."""
        stmt = select(User).where(User.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def update_user_by_id(
        self,
        user_id: int,
        fields: dict[str, Any],
    ) -> Optional[User]:
        """Update a user, or return None if not found."""
        user = await self.get_user_by_id(user_id)

        if user is None:
            return None

        for key, value in fields.items():
            setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def remove_user_by_id(self, user_id: int) -> Optional[User]:
        """Remove a user by ID, or return None if not found."""
        user = await self.get_user_by_id(user_id)

        if user is None:
            return None

        await self.db.delete(user)
        await self.db.commit()
        return user
