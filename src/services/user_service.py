"""Service layer providing business logic for managing User entities."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from libgravatar import Gravatar

from src.db.models import User
from src.db.repository import UsersRepository
from src.utils.logger import logger
from src.utils.security.password_utils import get_password_hash, verify_password

from .errors import UserConflictError, InvalidUserCredentialsError


class UserService:
    """Handles business logic related to users."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the service with a users repository."""
        self.repo = UsersRepository(db_session)

    async def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user."""
        # Check for conflicts
        errors: dict[str, str] = {}
        if await self.repo.get_user_by_username(username):
            errors["username"] = "Username is already taken."
        if await self.repo.get_user_by_email(email):
            errors["email"] = "User with such Email is already registered."
        if errors:
            raise UserConflictError(errors)

        # Generate hashed password
        hashed_password = get_password_hash(password)

        # Resolve avatar
        avatar = None
        try:
            gravatar = Gravatar(email)
            avatar = gravatar.get_image(
                size=200,
                use_ssl=True,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.info(
                "Failed to fetch Gravatar avatar based on user e-mail for user '%s': %s",
                username,
                str(e),
            )

        # Create a new user
        user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "avatar": avatar,
        }
        user = await self.repo.create_user(user_data)

        return user

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by ID or return None if not exists."""
        return await self.repo.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by username or return None if not exists."""
        return await self.repo.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by email or return None if not exists."""
        return await self.repo.get_user_by_email(email)

    async def validate_user_credentials(
        self, username: str, plain_password: str
    ) -> User:
        """Validate user credentials and return user ID"""
        user: Optional[User] = await self.get_user_by_username(username)

        if user is None:
            raise InvalidUserCredentialsError(f"User '{username}' does not exist")

        if not verify_password(plain_password, user.hashed_password):
            raise InvalidUserCredentialsError(
                f"Invalid password for the user '{username}'"
            )

        return user
