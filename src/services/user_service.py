"""Service layer providing business logic for managing User entities."""

from typing import Optional, Union, Any, Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar  # type: ignore[import]

from src.db.models import User
from src.db.models.enums.user_roles import UserRole
from src.db.repository import UsersRepository
from src.services.dtos import UserDTO
from src.services.errors import UserInactiveError, UserConflictError
from src.utils.constants import DEFAULT_SUPERADMIN_EMAIL, DEFAULT_SUPERADMIN_PASSWORD
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination
from src.utils.security.password_utils import get_password_hash, verify_password

from .contact_service import ContactService
from .dtos import UserWithStatsDTO
from .errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    UserConflictError,
    EmailChangeNotAllowedError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
    UserEmailIsAlreadyConfirmedError,
)


# TODO: Add email change flow
# ? Follow "Email change flow" marks in the code
# TODO: Separate module to follow SRP:
# e.g. src/services/user/ package
# * ├─ __init__.py  # reexport of the facade (UserService) if necessary
# * ├─ creation.py  # create_superuser, register_user, _create_user_common
# * ├─ update.py    # update_current_user, update_user_by_admin, update_user_by_admin_helpers
# * ├─ queries.py   # get_user_by_id, get_all_users, get_user_by_email/username
# * ├─ security.py  # confirm_user_email, password helpers, email flow helpers
# * ├─ delete.py    # delete_user_by_admin
# * └─ policies.py  # RolePolicy (at first stages may be simple)
# TODO: introduce RolePolicy class to handle all RolePolicy / PermissionGuard
# RolePolicy.ensure_can_modify(requester, target, field="role")
# RolePolicy.ensure_can_delete(requester, target)
# RolePolicy.ensure_can_create(requester, role)
# * I.e.:
# * "Users cannot update users"
# * "Moderators cannot update users"
# * "Admins cannot update admins"
# * "Non-superadmin cannot modify superadmin"
# * "Superadmin cannot downgrade superadmin"
# * "Admins cannot delete admins or superadmins"
# * "Superadmin cannot delete superadmin"
# * "Admins cannot create admins"
# * "Moderators cannot create users"
class UserService:
    """Handles business logic related to users."""

    def __init__(self, db_session: AsyncSession):
        """Initialize the service with a users repository."""
        self.repo = UsersRepository(db_session)

    async def create_superuser(self, username: str, email: str, password: str) -> None:
        """Create a superuser if it doesn't exist. Returns True if created."""
        if not email:
            raise InvalidUserCredentialsError(
                "Email for superadmin is empty or missing."
            )
        elif email == DEFAULT_SUPERADMIN_EMAIL:
            raise InvalidUserCredentialsError(
                "Email for superadmin is a default email and is invalid."
            )

        if not password:
            raise InvalidUserCredentialsError(
                "Password for superadmin is empty or missing."
            )
        elif password == DEFAULT_SUPERADMIN_PASSWORD:
            raise InvalidUserCredentialsError(
                "Password for superadmin is a default password and is invalid"
            )

        existing_user = await self.get_user_by_username(username)
        if existing_user:
            raise UserConflictError({"init": "Superuser already exists"})

        await self._create_user_common(
            creator=None,
            username=username,
            email=email,
            password=password,
            avatar=None,
            role=UserRole.SUPERADMIN,
            is_active=True,
        )

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
        role = UserService._validate_role_exists(role_str)

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

    async def confirm_user_email(self, user_id: int, email: str) -> User:
        """
        Validate that the user exists, matches the token data, and confirm email.

        Raises:
            InvalidUserCredentialsError: if user not found or email doesn't match
            UserEmailIsAlreadyConfirmedError: if user email has been confirmed already
        """
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise InvalidUserCredentialsError(
                f"User with provided user_id={user_id} not found"
            )

        # Check if user is active before confirming
        if not user.is_active:
            logger.warning(
                "Attempt to confirm email for inactive user %s",
                UserDTO.from_orm(user),
            )
            raise UserInactiveError("Cannot confirm email for inactive user")

        if user.email != email:
            raise InvalidUserCredentialsError(
                "Token email does not match current user email"
            )

        if user.is_email_confirmed:
            raise UserEmailIsAlreadyConfirmedError()

        updated_user = await self.repo.confirm_user_email_by_id(user_id)
        if not updated_user:
            # happens only if someone confirmed email in parallel
            raise InvalidUserCredentialsError(
                f"Failed to confirm email for user_id={user_id}"
            )

        logger.info("User email confirmed for user %s", UserDTO.from_orm(updated_user))

        return updated_user

    async def get_all_users(
        self, requester: UserDTO, pagination: Dict[str, int], filters: Dict[str, Any]
    ) -> Tuple[List[UserWithStatsDTO], int]:
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
                "Action is forbidden: %s %s attempted to view info about SUPERADMIN user %s",
                requester.role.value.upper(),
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
                    "Action is forbidden: %s attempted to view info about other inactive ADMIN user %s "
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

        update_user_data: Dict[str, Any] = {}

        # 1. Check provided data

        # password
        if password:
            UserService._validate_password_change(
                old_password, password, current_user.hashed_password
            )
            update_user_data["hashed_password"] = get_password_hash(password)

        # 2. Check for conflicts

        # Email conflicts with already registered email
        if email and email != current_user.email:
            # Email change is forbidden until proper email-change flow is implemented
            # ? Email change flow: Remove this error and add following additional checks:
            # ? add: await self._validate_email_conflict(current_user, email)
            # ? add: update_user_data["email"] = email
            raise EmailChangeNotAllowedError(
                "Email change is temporarily disabled until the email change flow is implemented."
            )

        # 3. Resolve avatar

        # Avatar (with fallback to gravatar if None)
        if avatar is not None and avatar != current_user.avatar:
            if email:
                update_user_data["avatar"] = UserService._try_fetch_gravatar(
                    email, log_user=current_user
                )
            else:
                update_user_data["avatar"] = avatar

        updated_user = await self.repo.update_user_by_id(
            current_user.id, update_user_data
        )
        if not updated_user:
            return None

        logger.debug(
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
        # 1. Check payload

        # 1.1 Check if empty

        if not update_data:
            # Nothing to update
            raise BadProvidedDataError(
                {"Provided data": "No fields provided to update."}
            )

        # Temporary guard to restrict email change until email change flow is not introduced
        # ? Email change flow: Remove this guard when email change flow is implemented
        if "email" in update_data:
            raise EmailChangeNotAllowedError(
                "Email change is temporarily disabled until the email change flow is implemented."
            )

        # 2. Fetch target user

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            return None

        # 3. Self-update logic case - restrict and refer to current user update endpoint

        if requester.id == user.id:
            logger.warning(
                (
                    "Action is forbidden: %s attempted to perform self-update via admin endpoint "
                    "of the following fields %s"
                ),
                requester,
                update_data.keys(),
            )
            raise UserRolePermissionError(
                (
                    "Self-update is not allowed via admin endpoint. "
                    "Use /me endpoint instead."
                )
            )

        # 4. Update of another user

        # 4.1 Requester / Target user role based restrictions

        # Users and moderators cannot use admin update of other users
        if requester.role in {UserRole.USER, UserRole.MODERATOR}:
            raise UserRolePermissionError(
                f"{requester.role.value} are not allowed to update users"
            )

        # Admin cannot modify other admins
        if requester.role == UserRole.ADMIN and user.role == UserRole.ADMIN:
            raise UserRolePermissionError("Admins cannot modify other admins")

        # Non-superadmin cannot modify superadmin user data
        if requester.role != UserRole.SUPERADMIN and user.role == UserRole.SUPERADMIN:
            logger.warning(
                (
                    "Action is forbidden: Non-superadmin %s requested update of SUPERADMIN %s "
                    "of the following fields: %s"
                ),
                requester,
                UserDTO.from_orm(user),
                update_data.keys(),
            )
            raise UserRolePermissionError("Cannot modify superadmin user")

        # 4.2 Allow-list payload data filtering

        allowed_fields = {
            "username",  # only superadmin
            "avatar",
            "role",  # only superadmin
            "is_active",
        }
        cleaned_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        if not cleaned_data:
            raise BadProvidedDataError(
                {"Provided data": "No allowed fields to update."}
            )

        # 4.3 Check resulting payload data and conflicts

        # Role exists
        if "role" in cleaned_data:
            cleaned_data["role"] = UserService._validate_role_exists(
                cleaned_data["role"]
            )

        # 4.4 Provided data / user role based restrictions

        # Admin cannot change usernames
        if "username" in cleaned_data and requester.role == UserRole.ADMIN:
            raise UserRolePermissionError("Admins cannot change usernames")

        # Only superadmin can change user role
        if "role" in cleaned_data:
            new_role = cleaned_data["role"]
            if requester.role != UserRole.SUPERADMIN:
                # No other user can perform user change action
                logger.warning(
                    "Action is forbidden: Non-superadmin %s attempted to change role of %s %s",
                    requester,
                    user.role.value.upper(),
                    UserDTO.from_orm(user),
                )
                raise UserRolePermissionError("Only superadmin can change user roles")
            elif user.role == UserRole.SUPERADMIN and new_role != UserRole.SUPERADMIN:
                # Superadmin can't level-down (downgrade) other superadmin role,
                # but still may lever-up (upgrade) it for other non-superadmin users
                logger.warning(
                    "Action is forbidden: SUPERADMIN %s attempted to change other SUPERADMIN %s role to %s",
                    requester,
                    UserDTO.from_orm(user),
                    new_role.upper(),
                )
                raise UserRolePermissionError(
                    "Superadmin cannot change another superadmin's role"
                )

        # 4.5. Perform update

        updated_user = await self.repo.update_user_by_id(user.id, cleaned_data)
        if not updated_user:
            return None

        logger.debug(
            "%s updated user %s with field data %s",
            requester,
            UserDTO.from_orm(user),
            {
                k: v
                for k, v in cleaned_data.items()
                if v is not None and k not in {"password", "hashed_password"}
            },
        )

        # 5. Get user contacts count
        contacts_count = await contacts_service.get_contacts_count(user.id)

        # 6. Return result (DTO with contacts_count)
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

        # 3.2 Moderator cannot delete anyone
        if requester.role == UserRole.MODERATOR:
            raise UserRolePermissionError("Moderators are not allowed to delete users")

        # 3.3 Superadmin cannot delete other superadmins
        if requester.role == UserRole.SUPERADMIN and user.role == UserRole.SUPERADMIN:
            raise UserRolePermissionError("Superadmin cannot delete another superadmin")

        # 3.3 Admin cannot delete other admins or superadmins
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

        logger.info(
            "%s %s deleted %s %s",
            requester.role.value.upper(),
            requester,
            deleted_user.role.value.upper(),
            UserDTO.from_orm(user),
        )

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
        avatar = avatar or UserService._try_fetch_gravatar(email, log_user=creator)

        # Create new user data
        new_user_data = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "avatar": avatar,
            "is_active": is_active,
            "role": role,
            "is_email_confirmed": False,
        }
        new_user = await self.repo.create_user(new_user_data)

        creator_role = f"{creator.role.value.upper()} " if creator else ""
        creator_info = creator if creator else "Anonymous user"
        new_user_info = UserDTO.from_orm(new_user)
        logger.info(
            "%s%s created a new %s %s",
            creator_role,
            creator_info,
            new_user_info.role.value.upper(),
            new_user_info,
        )

        return new_user

    def _validate_creation_permissions(
        self, creator: UserDTO, role: UserRole, username: str, email: str
    ) -> None:
        """
        Ensure the creator has permission to assign the given role.

        Rules:
        - SUPERADMIN creation is always restricted.
        - ADMIN cannot create other ADMINS or SUPERADMINS.
        - MODERATOR cannot create anyone.
        """
        # Restrict creating superadmin users at all
        if role == UserRole.SUPERADMIN:
            # User attempted to create a Superadmin user (to gain full app permissions?).
            logger.warning(
                "%s attempted to create SUPERADMIN (username=%s, email=%s)",
                creator,
                username,
                email,
            )
            raise UserRolePermissionError("Creating of superadmin is restricted")

        # Moderators cannot create any users at all
        if creator.role == UserRole.MODERATOR:
            logger.warning(
                "%s (MODERATOR) attempted to create user (username=%s, role=%s)",
                creator,
                username,
                role,
            )
            raise UserRolePermissionError("Moderators are not allowed to create users")

        # Restrict creation of admin users by other admins
        if creator.role == UserRole.ADMIN and role in {
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
        }:
            logger.warning(
                "%s (ADMIN) attempted to create user with role=%s (username=%s)",
                creator,
                role,
                username,
            )
            raise UserRolePermissionError(
                "Admins cannot create other admins or superadmins"
            )

    async def _validate_email_conflict(self, current_user: UserDTO, email: str) -> None:
        existing_user = await self.repo.get_user_by_email(email)
        if existing_user and existing_user.id != current_user.id:
            # User tries to assign email to an existing email in the system
            # (sniffing to check if there is a user with such email?)
            logger.warning(
                ("%s attempted to change email to email of the existing user %s"),
                current_user,
                UserDTO.from_orm(existing_user),
            )
            raise UserConflictError({"email": "Email already taken"})

    @staticmethod
    def _validate_password_change(
        old_password: Optional[str], new_password: str, hashed_old: str
    ) -> None:
        """
        Validate old password before updating to new password.

        Raises BadProvidedDataError if old password is missing or same as new.
        Raises InvalidUserCredentialsError if old password doesn't match.
        """
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

    @staticmethod
    def _validate_role_exists(role: Optional[Union[str, UserRole]]) -> UserRole:
        """Ensure provided role exists in UserRole enum."""
        if not role:
            raise UserRoleIsInvalidError("Role cannot be empty or None")

        if isinstance(role, UserRole):
            return role

        try:
            return UserRole(role)
        except ValueError as exc:
            raise UserRoleIsInvalidError(f"Invalid role: '{role}'") from exc

    @staticmethod
    def _try_fetch_gravatar(email: str, log_user: Optional[UserDTO]) -> Optional[str]:
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
            return None
