"""Service layer providing business logic for managing User entities."""

from typing import Optional, Union, Any, Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.db.models import User
from src.db.models.enums.user_roles import UserRole
from src.db.repository import UsersRepository
from src.services.dtos import UserDTO
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination
from src.utils.security.password_utils import get_password_hash, verify_password

from .contact_service import ContactService
from .dtos import UserWithStatsDTO
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
        """
        Create a new user (public access).

        Raises:
            UserConflictError: if username or email already exist.
        """
        return await self._create_user_common(
            creator=None,
            username=username,
            email=email,
            password=password,
            avatar=avatar,
            role=UserRole.USER,
            is_active=True,
        )

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

    async def register_user_by_admin(
        self,
        creator: UserDTO,
        username: str,
        email: str,
        password: str,
        avatar: Optional[str] = None,
        role_str: str = UserRole.USER.value,
        is_active: bool = True,
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

    async def get_all_users(
        self, requester: UserDTO, pagination: Dict[str, int], filters: Dict[str, Any]
    ) -> Tuple[list[UserWithStatsDTO], int]:
        """
        Return a paginated list of users with contact counts.

        Optional filters may be applied to the search.

        Business logic:
        - SUPERADMIN sees everyone and all contact counts.
        - ADMIN sees other admins and users, but contact counts are hidden (None) for admins.
        """

        # Get all existing users with total users count
        skip, limit = get_pagination(pagination)
        users_with_contacts_counts, total_count = await self.repo.get_all_users(
            skip,
            limit,
            **filters,
            # exclude_user_id=requester.id,  # Option to hide current user in search results
            requester_role=requester.role,
        )

        # Check for empty users list
        if total_count == 0:
            return [], 0

        # Role-based visibility logic
        # Show contact counts and other personal info for any user when requester is a SUPERADMIN
        # Hide contact counts and other personal info for other admins when requester is an ADMIN
        result: List[UserWithStatsDTO] = []
        for user, contacts_count in users_with_contacts_counts:
            # Flag whether to hide additional info from user
            show_full = (
                requester.role == UserRole.SUPERADMIN
                or user.id == requester.id
                or user.role == UserRole.USER
            )

            if show_full:
                result.append(
                    UserWithStatsDTO.from_orm_with_count(user, contacts_count)
                )
            else:
                result.append(
                    UserWithStatsDTO.from_orm_with_count(user, None, hide_personal=True)
                )

        return result, total_count

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by ID or return None if not exists."""
        return await self.repo.get_user_by_id(user_id)

    async def get_user_by_id_for_admin(
        self,
        requester: UserDTO,
        user_id: int,
        contacts_service: ContactService,
    ) -> Optional[UserWithStatsDTO]:
        """
        Retrieve a single user by ID, applying role-based visibility rules.

        - SUPERADMIN can see any user.
        - ADMIN cannot see other inactive admins.
        - Contact counts are hidden for admins viewing other admins.
        """
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            return None

        # Restrict providing superadmin data
        if user.role == UserRole.SUPERADMIN and requester.id != user.id:
            logger.warning(
                "%s requested info about SUPERADMIN user %s while not allowed to view that user",
                requester,
                UserDTO.from_orm(user),
            )
            return None

        # If current user is admin - do not provide inactive admin user data
        if (
            requester.role == UserRole.ADMIN
            and user.role == UserRole.ADMIN
            and not user.is_active
        ):
            logger.warning(
                (
                    "%s requested info about other inactive ADMIN user %s "
                    "while not allowed to view that user"
                ),
                requester,
                UserDTO.from_orm(user),
            )
            return None

        # Define flag, if to show full or partial user information
        show_full = (
            requester.role == UserRole.SUPERADMIN
            or requester.id == user.id
            or user.role == UserRole.USER
        )

        if show_full:
            contacts_count = await contacts_service.get_contacts_count(user.id)
            return UserWithStatsDTO.from_orm_with_count(user, contacts_count)

        return UserWithStatsDTO.from_orm_with_count(user, hide_personal=True)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username or return None if not exists."""
        return await self.repo.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email or return None if not exists."""
        return await self.repo.get_user_by_email(email)

    async def update_current_user(
        self,
        current_user: UserDTO,
        contacts_service: ContactService,
        email: Optional[str] = None,
        old_password: Optional[str] = None,
        password: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> Optional[UserWithStatsDTO]:
        """
        Update a contact fully or partially.

        Raises:
        - InvalidUserCredentialsError: if old password is not correct and can't
        - BadProvidedDataError: if any field has bad or improper value
        - UserConflictError: if new email conflicts with other registered email
        """

        update_user_data = {}

        # 1. Check provided data

        # password
        if password:
            self._validate_password_change(
                old_password, password, current_user.hashed_password
            )
            update_user_data["hashed_password"] = get_password_hash(password)

        # email
        if email and email == current_user.email:
            raise BadProvidedDataError(
                {"email": "New email can't be the same as the current one"}
            )

        # 2. Check for conflicts

        # Email conflicts with already registered email
        if email:
            await self._validate_email_conflict(current_user, email)
            update_user_data["email"] = email

        # 3. Resolve avatar

        # Avatar (with fallback to gravatar if None)
        if avatar is not None and avatar != current_user.avatar:
            if email:
                update_user_data["avatar"] = self._try_fetch_gravatar(
                    email, log_user=current_user
                )
            else:
                update_user_data["avatar"] = avatar

        updated_user = await self.repo.update_user_by_id(
            current_user.id, update_user_data
        )
        if not updated_user:
            return None

        logger.info(
            "%s performed self update using admin endpoint with data %s",
            current_user,
            {
                "email": email,
                "password": "<hidden>" if password else None,
                "avatar": avatar,
            },
        )

        # Return updated user (DTO with contacts_count)
        contacts_count = await contacts_service.get_contacts_count(current_user.id)
        return UserWithStatsDTO.from_orm_with_count(updated_user, contacts_count)

    async def update_user_by_admin(
        self,
        requester: UserDTO,
        user_id: int,
        update_data: dict,
        contacts_service: ContactService,
    ) -> Optional[UserWithStatsDTO]:
        """
        Update user as admin/superadmin with role-based constraints.
        - Superadmin: can update any fields, including role.
        - Admin: can update users, but cannot update other admins or any role field.
            Admin may update own profile except role.
        """
        # 1. Fetch target user

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            return None

        # 2. Self-update case - delegate to current user update

        if requester.id == user.id:
            # Superadmin can update themselves (with limitations)
            # Prevent Superadmin from locking themselves
            if requester.role == UserRole.SUPERADMIN:
                # Protect against changing role or deactivation
                if "role" in update_data and update_data["role"] != UserRole.SUPERADMIN:
                    raise UserRolePermissionError(
                        "Superadmin cannot remove their own superadmin role"
                    )
                if "is_active" in update_data and not update_data["is_active"]:
                    raise UserRolePermissionError(
                        "Superadmin cannot deactivate themselves"
                    )

            # Admin cannot change role or active status for themselves
            elif requester.role == UserRole.ADMIN:
                if "role" in update_data and update_data["role"] != user.role:
                    raise UserRolePermissionError("Admin cannot change own role")
                if (
                    "is_active" in update_data
                    and update_data["is_active"] != user.is_active
                ):
                    raise UserRolePermissionError(
                        "Admin cannot change active status themselves"
                    )

            log_data = {
                "email": update_data.get("email"),
                "password": "<hidden>" if update_data.get("password") else None,
                "avatar": update_data.get("avatar"),
                "role": update_data.get("role"),
                "is_active": update_data.get("is_active"),
            }
            log_data = {
                k: v
                for k, v in log_data.items()
                if v is not None and k not in {"password", "hashed_password"}
            }
            logger.info(
                "%s updated self via admin endpoint with data %s", requester, log_data
            )

            return await self.update_current_user(
                current_user=requester,
                email=update_data.get("email"),
                old_password=update_data.get("old_password"),
                password=update_data.get("password"),
                avatar=update_data.get("avatar"),
                contacts_service=contacts_service,
            )

        # 3. Update of another user

        # 3.1 Check role-based restrictions

        # Superadmin cannot modify other superadmin user data
        if requester.role == UserRole.SUPERADMIN and user.role == UserRole.SUPERADMIN:
            if "role" in update_data and update_data["role"] != UserRole.SUPERADMIN:
                raise UserRolePermissionError("Cannot change another superadmin's role")
        # Other users cannot modify superadmin user data
        if requester.role != UserRole.SUPERADMIN and user.role == UserRole.SUPERADMIN:
            logger.warning(
                "%s requested update of SUPERADMIN user %s while not allowed",
                requester,
                UserDTO.from_orm(user),
            )
            raise UserRolePermissionError("Cannot modify superadmin user")

        # Admin cannot modify other admins
        if requester.role == UserRole.ADMIN and user.role == UserRole.ADMIN:
            raise UserRolePermissionError("Admins cannot modify other admins")

        # Admin cannot change usernames
        if requester.role == UserRole.ADMIN and "username" in update_data:
            raise UserRolePermissionError("Admins cannot change usernames")

        # Only superadmin can change role
        if "role" in update_data and requester.role != UserRole.SUPERADMIN:
            raise UserRolePermissionError("Only superadmin can change user roles")

        # 3.2 Check provided data and conflicts

        # role
        if "role" in update_data:
            update_data["role"] = self._validate_role_exists(update_data["role"])

        # email
        if "email" in update_data and update_data["email"] != user.email:
            await self._validate_email_conflict(
                UserDTO.from_orm(user), update_data["email"]
            )

        # 4. Perform actual update

        allowed = {
            "username",
            "email",
            "avatar",
            "hashed_password",
            "role",
            "is_active",
        }
        cleaned = {k: v for k, v in update_data.items() if k in allowed}
        updated_user = await self.repo.update_user_by_id(user.id, cleaned)
        if not updated_user:
            return None

        logger.info(
            "%s updated user %s with data %s",
            requester,
            UserDTO.from_orm(user),
            {
                k: v
                for k, v in update_data.items()
                if v is not None and k not in {"password", "hashed_password"}
            },
        )

        # 5. Return updated user (DTO with contacts_count)
        contacts_count = await contacts_service.get_contacts_count(user.id)
        return UserWithStatsDTO.from_orm_with_count(updated_user, contacts_count)

    async def delete_user_by_admin(
        self,
        requester: UserDTO,
        user_id: int,
        contacts_service: Optional[ContactService] = None,
    ) -> Optional[UserWithStatsDTO]:
        """
        Delete a user by admin or superadmin, with strict role-based rules.

        Rules:
        - SUPERADMIN can delete any user except themselves and other SUPERADMINs.
        - ADMIN can delete only regular USERs, not themselves or other admins.
        - USERs cannot delete anyone.

        Raises:
            UserRolePermissionError: if requester is not allowed to delete the target user.
        """
        # 1. Fetch the target user

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            return None

        # 2. Prevent self-deletion

        if requester.id == user.id:
            raise UserRolePermissionError("Users cannot delete themselves")

        # 3. Role-based restrictions

        # 3.1 User cannot delete anyone
        if requester.role == UserRole.USER:
            raise UserRolePermissionError(
                "Regular users are not allowed to delete users"
            )

        # 3.2 Superadmin restrictions
        if requester.role == UserRole.SUPERADMIN and user.role == UserRole.SUPERADMIN:
            raise UserRolePermissionError("Superadmin cannot delete another superadmin")

        # 3.3 Admin restrictions
        if requester.role == UserRole.ADMIN and user.role in {
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
        }:
            raise UserRolePermissionError("Admins cannot delete admins or superadmins")

        # 4. Get contacts count before deletion

        contacts_count = (
            await contacts_service.get_contacts_count(user.id)
            if contacts_service
            else None
        )

        # 5. Perform deletion

        deleted_user = await self.repo.remove_user_by_id(user.id)
        if not deleted_user:
            return None

        # 6. Logging

        logger.info("%s deleted user %s", requester, UserDTO.from_orm(user))

        # 7. Return deleted user info with stats
        return UserWithStatsDTO.from_orm_with_count(
            deleted_user,
            contacts_count,
            hide_personal=True,
        )

    async def _create_user_common(
        self,
        creator: Optional[UserDTO],
        username: str,
        email: str,
        password: str,
        avatar: Optional[str],
        role: UserRole,
        is_active: bool = True,
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
        avatar = avatar or self._try_fetch_gravatar(email, log_user=creator)

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

    def _validate_password_change(
        self, old_password: Optional[str], new_password: str, hashed_old: str
    ) -> None:
        """Raise an exception if password change validation fails."""
        if not old_password:
            raise BadProvidedDataError(
                {"password": "Old password is required to change password"}
            )
        if new_password == old_password:
            # Additional check of invalid scenario - should be handled by frontend
            raise BadProvidedDataError(
                {"password": "New password can't be the same as the old one"}
            )
        if not verify_password(old_password, hashed_old):
            # Check for user authorization to change password
            logger.warning(
                "User failed to pass old password validation (possible stolen token)"
            )
            raise InvalidUserCredentialsError("Incorrect old password")

    async def _validate_email_conflict(self, current_user: UserDTO, email: str) -> None:
        existing_user = await self.repo.get_user_by_email(email)
        if existing_user and existing_user.id != current_user.id:
            # Potentially suspicious activity requiring logging
            # User tries to assign email to an existing email in the system
            # (sniffing to check if there is a user with such email?)
            logger.warning(
                ("%s tried to change email to email of the existing user %s"),
                current_user,
                UserDTO.from_orm(existing_user),
            )
            raise UserConflictError({"email": "Email already taken"})

    def _validate_role_exists(self, role: Optional[Union[str, UserRole]]) -> UserRole:
        """Ensure provided role exists in UserRole enum."""
        if not role:
            raise UserRoleIsInvalidError("Role cannot be empty or None")

        if isinstance(role, UserRole):
            return role

        try:
            return UserRole(role)
        except ValueError as exc:
            raise UserRoleIsInvalidError(f"Invalid role: '{role}'") from exc

    def _try_fetch_gravatar(
        self, email: str, log_user: Optional[UserDTO]
    ) -> Optional[str]:
        """Fetch gravatar avatar"""
        if not email:
            return None

        try:
            gravatar = Gravatar(email)
            return gravatar.get_image(size=200, use_ssl=True)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug(
                "Failed to fetch Gravatar for %s: %s", log_user or "Unknown", e
            )
