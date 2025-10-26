"""Service layer providing business logic for managing User entities."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from libgravatar import Gravatar

from src.db.models import User
from src.db.models.enums.user_roles import UserRole
from src.db.repository import UsersRepository
from src.services.dtos import UserDTO
from src.utils.logger import logger
from src.utils.security.password_utils import get_password_hash, verify_password

from .errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    UserConflictError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
)


class UserService:
    """Handles business logic related to users."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the service with a users repository."""
        self.repo = UsersRepository(db_session)

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        avatar: Optional[str] = None,
    ) -> User:
        """Create a new user (public access)."""
        return await self._create_user_common(
            creator=None,
            username=username,
            email=email,
            password=password,
            avatar=avatar,
            role=UserRole.USER,
            is_active=True,
        )

    async def register_user_by_admin(
        self,
        creator: UserDTO,
        username: str,
        email: str,
        password: str,
        avatar: Optional[str] = None,
        role_str: str = UserRole.USER.value,
        is_active: Optional[bool] = True,
    ) -> User:
        """Create a new user by an admin or superadmin."""

        # Provided role check
        role = self._validate_role_exists(role_str)

        # Role restriction logic check
        self._validate_creation_permissions(creator, role, username, email)

        return await self._create_user_common(
            creator=creator,
            username=username,
            email=email,
            password=password,
            avatar=avatar,
            role=role,
            is_active=is_active,
        )

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Retrieve a user by ID or return None if not exists."""
        return await self.repo.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Retrieve a user by username or return None if not exists."""
        return await self.repo.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by email or return None if not exists."""
        return await self.repo.get_user_by_email(email)

    async def update_user(
        self,
        user: UserDTO,
        email: Optional[str] = None,
        old_password: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update a contact fully or partially.

        Raises:
        - InvalidUserCredentialsError: if old password is not correct and can't
        - BadProvidedDataError: if any field has bad or improper value
        - UserConflictError: if new email conflicts with other registered email
        """

        user_new_data = {}

        # 1. Validate provided data values and user authorization

        data_errors: dict[str, str] = {}

        # Check provided passwords values and user authorization
        if password:
            if not old_password:
                data_errors["password"] = "Old password is required to change password"
            elif password == old_password:
                # Additional check of invalid scenario - should be handled by frontend
                data_errors["password"] = (
                    "New password can't be the same as the old one"
                )
            else:
                # Check for user authorization
                if not verify_password(old_password, user.hashed_password):
                    # Potentially suspicious activity requiring logging
                    # User failed to confirm old password (stolen token?)
                    logger.warning(
                        (
                            "User with id = %d failed to pass old password validation "
                            "while updating user data"
                        ),
                        user.id,
                    )
                    raise InvalidUserCredentialsError("Incorrect old password")
            user_new_data["hashed_password"] = get_password_hash(password)

        # Check provided email value
        if email and email == user.email:
            data_errors["email"] = "New email can't be the same as the current one"

        if data_errors:
            raise BadProvidedDataError(data_errors)

        # 2. Check for conflicts

        conflict_errors: dict[str, str] = {}

        # Check for email conflicts with already registered user emails
        if email:
            existing_user_with_such_email = await self.repo.get_user_by_email(email)
            if existing_user_with_such_email:
                # Potentially suspicious activity requiring logging
                # User tries to assign email to an existing email in the system
                # (sniffing to check if there is a user with such email?)
                logger.info(
                    (
                        "User with id = %d tried to change email "
                        "to email of the existing user with id = %d"
                    ),
                    user.id,
                    existing_user_with_such_email.id,
                )
                conflict_errors["email"] = "Email already taken"

            user_new_data["email"] = email

        if conflict_errors:
            raise UserConflictError(conflict_errors)

        # 3. Resolve avatar

        if avatar != user.avatar:
            if avatar is None or not avatar:
                # Explicitly remove existing avatar
                if email:
                    # Try to replace avatar with gravatar (if email provided)
                    user_new_data["avatar"] = self._try_fetch_gravatar(
                        email, user.username
                    )
                else:
                    # Just assign None to avatar (leave it for fallback avatar replaced by frontend)
                    user_new_data["avatar"] = avatar
            else:
                # Assign provided custom avatar
                user_new_data["avatar"] = avatar

        return await self.repo.update_user_by_id(user.id, user_new_data)

    async def validate_user_credentials(
        self, username: str, plain_password: str
    ) -> User:
        """
        Validate user credentials and return user ID

        Raises:
        - InvalidUserCredentialsError: if any credential is not valid
        """
        user: Optional[User] = await self.get_user_by_username(username)

        if user is None:
            raise InvalidUserCredentialsError(f"User '{username}' does not exist")

        if not verify_password(plain_password, user.hashed_password):
            raise InvalidUserCredentialsError(
                f"Invalid password for the user '{username}'"
            )

        return user

    async def _create_user_common(
        self,
        creator: Optional[UserDTO],
        username: str,
        email: str,
        password: str,
        avatar: Optional[str],
        role: UserRole,
        is_active: Optional[bool] = True,
    ) -> User:
        """Common internal method for user creation logic."""

        # Conflicts check
        errors: dict[str, str] = {}
        if await self.repo.get_user_by_username(username):
            errors["username"] = "Username is already taken"
        if await self.repo.get_user_by_email(email):
            errors["email"] = "User with such Email is already registered"
        if errors:
            raise UserConflictError(errors)

        # Hash password
        hashed_password = get_password_hash(password)

        # Avatar (fallback to gravatar)
        avatar = avatar or self._try_fetch_gravatar(email, username)

        # Create new user data
        new_user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "avatar": avatar,
            "is_active": is_active,
            "role": role,
        }
        new_user = await self.repo.create_user(new_user_data)

        creator_info = str(creator) if creator else "Anonymous user"
        new_user_info = str(UserDTO.from_orm(new_user))
        logger.info("New user created by %s: new user %s", creator_info, new_user_info)

        return new_user

    def _validate_role_exists(self, role_str: Optional[str]) -> UserRole:
        """Ensure provided role exists in UserRole enum."""
        if not role_str:
            raise UserRoleIsInvalidError("Role cannot be empty or None")

        try:
            return UserRole(role_str)
        except ValueError as exc:
            raise UserRoleIsInvalidError(f"Invalid role: '{role_str}'") from exc

    def _validate_creation_permissions(
        self, creator: UserDTO, role: UserRole, username: str, email: str
    ) -> None:
        """Ensure creator has permissions for assigning the given role."""
        # Restrict creating superadmin users at all
        if role == UserRole.SUPERADMIN:
            # Potentially suspicious activity requiring logging
            # User tried to create a Superadmin user (to gain full app permissions?).
            logger.warning(
                "%s attempted to create SUPERADMIN (username=%s, email=%s)",
                creator,
                username,
                email,
            )
            raise UserRolePermissionError("Creating of superadmin is restricted")

        # Restrict creation of admin users by other admins
        if creator.role == UserRole.ADMIN and role == UserRole.ADMIN:
            logger.warning(
                "%s attempted to create another ADMIN user (username=%s)",
                creator,
                username,
            )
            raise UserRolePermissionError(
                "Admin users are not allowed to create other admins"
            )

    def _try_fetch_gravatar(
        self, email: str, log_username: Optional[str] = "<username>"
    ) -> Optional[str]:
        """Fetch gravatar avatar"""
        if not email:
            return None

        try:
            gravatar = Gravatar(email)
            return gravatar.get_image(size=200, use_ssl=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("Failed to fetch Gravatar for %s: %s", log_username, e)
