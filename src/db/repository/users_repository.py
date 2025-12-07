"""
Repository layer for User entities.

Provides asynchronous CRUD operations and query helpers.

This layer encapsulates all database logic, isolating it from business and routing layers.
"""

from typing import Optional, Any, List, Dict, Tuple

from sqlalchemy import select, update, func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, Contact
from src.db.models.enums.user_roles import UserRole

from src.api.schemas.users.enums import UserFilterRole


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

    async def get_users_total_count(self) -> int:
        """Return the total number of non-superadmin users."""
        result = await self.db.execute(
            select(func.count())  # pylint: disable=E1102
            .select_from(User)
            .filter(User.role != UserRole.SUPERADMIN)
        )
        return result.scalar() or 0

    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 50,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[UserFilterRole] = None,
        is_active: Optional[bool] = None,
        inactive_last: bool = False,
        exclude_user_id: Optional[int] = None,
        requester_role: UserRole = UserRole.USER,
    ) -> Tuple[List[Tuple[User, int]], int]:
        """
        Return a paginated list of users with total contact count for each,
        along with the total count for pagination.

        This query performs:
        - Filtering by optional parameters (case-insensitive partial matches)
        - Exclusion of SUPERADMIN users
        - LEFT JOIN to the contacts table to count associated contacts
        - Aggregation and pagination

        Note: This method executes two SQL queries (count + paginated data).
        """
        # --- Base statements ---

        count_stmt = select(func.count()).select_from(User)  # pylint: disable=E1102

        users_stmt = select(
            User,
            func.count(func.distinct(Contact.id)).label(  # pylint: disable=E1102
                "contacts_count"
            ),
        ).outerjoin(Contact, Contact.user_id == User.id)

        # --- Filters ---

        filters = []

        # Role filters

        # Show certain user roles
        filters.append(
            or_(
                User.role == UserRole.ADMIN,
                User.role == UserRole.MODERATOR,
                User.role == UserRole.USER,
            )
        )

        # Hide from admin user other inactive admins
        if requester_role == UserRole.ADMIN:
            filters.append(~((User.role == UserRole.ADMIN) & (User.is_active is False)))

        # Optional filters

        if exclude_user_id:
            filters.append(User.id != exclude_user_id)
        if username:
            filters.append(User.username.ilike(f"%{username}%"))
        if email:
            filters.append(User.email.ilike(f"%{email}%"))
        if role:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        if filters:
            count_stmt = count_stmt.filter(*filters)
            users_stmt = users_stmt.filter(*filters)

        # --- Total users count ---

        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        if total_count == 0:
            return [], 0

        # --- Users ---

        # Grouping (skip for count)
        users_stmt = users_stmt.group_by(User.id)

        # Ordering (skip for count)
        # Custom ordering of roles for admin UI: ADMIN → MODERATOR → USER
        role_custom_order = case(
            (User.role == UserRole.ADMIN, 1),
            (User.role == UserRole.MODERATOR, 2),
            (User.role == UserRole.USER, 3),
            else_=99,
        )
        if inactive_last:
            users_stmt = users_stmt.order_by(
                role_custom_order, User.is_active.desc(), func.lower(User.username)
            )
        else:
            users_stmt = users_stmt.order_by(
                role_custom_order, func.lower(User.username)
            )

        # Pagination
        users_stmt = users_stmt.offset(skip).limit(limit)

        # Resulting users list
        users_result = await self.db.execute(users_stmt)
        users_list = list(users_result.tuples().all())

        return users_list, total_count

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Return a single user by ID, or None if not found."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Return a single user by username, or None if not found."""
        stmt = select(User).where(func.lower(User.username) == username.lower())
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Return a single user by email (case insensitive), or None if not found."""
        stmt = select(User).where(func.lower(User.email) == email.lower())
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

        valid_columns = {column.name for column in User.__table__.columns}
        for key, value in fields.items():
            if key in valid_columns:
                setattr(user, key, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def confirm_user_email_by_id(self, user_id: int) -> Optional[User]:
        """Confirm a user's email, or return None if user not found or confirmed already."""
        # Use atomic update to avoid race conditions
        stmt = (
            update(User)
            .where(User.id == user_id, User.is_email_confirmed.is_(False))
            .values(is_email_confirmed=True)
            .returning(User)  # returns the updated row
        )
        result = await self.db.execute(stmt)
        updated_user = result.scalars().first()

        if updated_user is None:
            # either no user or email has been confirmed already
            return None

        await self.db.commit()
        await self.db.refresh(updated_user)
        return updated_user

    async def remove_user_by_id(self, user_id: int) -> Optional[User]:
        """Remove a user by ID, or return None if not found."""
        user = await self.get_user_by_id(user_id)

        if user is None:
            return None

        await self.db.delete(user)
        await self.db.commit()
        return user
