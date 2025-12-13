"""Service layer providing business logic for managing User entities."""

from typing import Optional, Union, Any, Mapping, Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.models.enums.user_roles import UserRole
from src.db.repository import UsersRepository
from src.providers.avatar_provider import GravatarProvider
from src.providers.cache_provider.user_cache import UserRedisCacheProvider
from src.providers.errors import GravatarResolveError
from src.utils.constants import DEFAULT_SUPERADMIN_EMAIL, DEFAULT_SUPERADMIN_PASSWORD
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination
from src.utils.security.password_utils import get_password_hash, verify_password

from .contact_service import ContactService
from .dtos import UserDTO, UserWithStatsDTO
from .errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    EmailChangeNotAllowedError,
    UserConflictError,
    UserInactiveError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
    UserEmailIsAlreadyConfirmedError,
)
from .markers import AppInitActor, APP_INIT_ACTOR, NOT_PROVIDED


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

    def __init__(
        self,
        db_session: AsyncSession,
        *,
        avatar_provider: Optional[GravatarProvider] = None,
        user_cache: Optional[UserRedisCacheProvider] = None,
    ) -> None:
        """Initialize the service with a users repository and other dependencies."""
        self.repo = UsersRepository(db_session)
        self.user_cache = user_cache
        self.avatar_provider = avatar_provider or GravatarProvider()

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
                {"old_password": "Old password is required to change password"}
            )
        if not new_password:
            raise BadProvidedDataError({"new_password": "New password can't be empty"})
        if new_password == old_password:
            # Additional check of invalid scenario - should be handled by frontend
            raise BadProvidedDataError(
                {"new_password": "New password can't be the same as the old one"}
            )
        if not verify_password(old_password, hashed_old):
            # Check for user authorization to change password
            logger.warning(
                "User failed to pass old password validation (possible stolen token)"
            )
            raise InvalidUserCredentialsError("Incorrect current password")

    @staticmethod
    def _validate_role_exists(role: Optional[Union[str, UserRole]]) -> UserRole:
        """
        Ensure provided role exists in UserRole enum.

        Returns: UserRole instance

        Raises:
         - UserRoleIsInvalidError if role is invalid, empty or None
        """
        if not role:
            raise UserRoleIsInvalidError("Role cannot be empty or None")

        if isinstance(role, UserRole):
            return role

        try:
            return UserRole(role)
        except ValueError as exc:
            raise UserRoleIsInvalidError(f"Invalid role: '{role}'") from exc

    async def create_superuser(self, username: str, email: str, password: str) -> None:
        """Create a superuser if it doesn't exist. Returns True if created."""
        if not email:
            raise BadProvidedDataError(
                {"email": "Email for superadmin is empty or missing."}
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
            creator=APP_INIT_ACTOR,
            username=username,
            email=email,
            password=password,
            role=UserRole.SUPERADMIN,
            is_active=True,
        )

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
    ) -> UserDTO:
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
            role=UserRole.USER,
            is_active=True,
        )

    async def register_user_by_admin(
        self,
        creator: UserDTO,
        username: str,
        email: str,
        password: str,
        role_str: str = UserRole.USER.value,
        is_active: bool = True,
    ) -> UserDTO:
        """Create a new user by an admin or superadmin."""

        # Provided role check
        role = UserService._validate_role_exists(role_str)

        # Role restriction logic check
        self._validate_creation_permissions(creator, role, username, email)

        # Get user from DB
        return await self._create_user_common(
            creator=creator,
            username=username,
            email=email,
            password=password,
            role=role,
            is_active=is_active,
        )

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

    async def get_user_by_id(self, user_id: int) -> Optional[UserDTO]:
        """Retrieve a user dto by ID or return None if not exists."""
        # 1. Try get user from cache
        if self.user_cache:
            user_cached: Optional[UserDTO] = await self.user_cache.get_user(user_id)
            if user_cached is not None:
                logger.debug("[CACHE HIT] User for user_id=%s", user_cached.id)
                return user_cached
            logger.debug("[CACHE MISS] User for user_id=%s", user_id)
        else:
            logger.debug("[CACHE ERROR] User cache is disabled")

        # 2. If not in cache --> request from DB
        user_orm = await self.repo.get_user_by_id(user_id)
        if not user_orm:
            return None

        # 3. Convert ORM to DTO object
        user_dto = UserDTO.from_orm(user_orm)

        # 4. Save to cache
        if self.user_cache:
            await self.user_cache.set_user(user_id, user_dto)

        return user_dto

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
                    "Action is forbidden: "
                    "%s attempted to view info about other inactive ADMIN user %s "
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

    async def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """Retrieve a user by username or return None if not exists."""
        user_orm = await self.repo.get_user_by_username(username)
        return UserDTO.from_orm(user_orm) if user_orm else None

    async def get_user_by_email(self, email: str) -> Optional[UserDTO]:
        """Retrieve a user by email or return None if not exists."""
        user_orm: Optional[User] = await self.repo.get_user_by_email(email)
        return UserDTO.from_orm(user_orm) if user_orm else None

    async def update_user_avatar(
        self,
        target_user: UserDTO,
        new_avatar_value: Optional[str],
    ) -> Optional[str]:
        """
        Update current user avatar value in DB.

        Args:
            current_user: user performing the change
            new_avatar_value: a URL or None provided by FileService

        Returns:
            Updated avatar URL or None if user disappeared.

        Raises:
            BadProvidedDataError: if no actual changes.
        """
        # 1. Normalize
        normalized = (
            new_avatar_value.strip() if isinstance(new_avatar_value, str) else None
        )

        # 2. Update user in DB
        updated_user = await self.repo.update_user_by_id(
            target_user.id, {"avatar": normalized}
        )
        if not updated_user:
            return None
        logger.debug(
            "%s changed avatar: %s -> %s",
            target_user,
            target_user.avatar,
            normalized,
        )

        # 3. Update user cache
        if self.user_cache:
            await self.user_cache.set_user(
                target_user.id, UserDTO.from_orm(updated_user)
            )

        # 4. Return updated user avatar url string
        return updated_user.avatar

    async def update_user_password(
        self,
        target_user: UserDTO,
        current_password: str,
        new_password: str,
        contacts_service: ContactService,
    ) -> Optional[UserWithStatsDTO]:
        """
        Update a current user password.

        Raises:
        - BadProvidedDataError: if any field has bad or improper value
        - InvalidUserCredentialsError: if old password is not correct or doesn't match
        """
        # 1. Validate provided password data
        UserService._validate_password_change(
            current_password, new_password, target_user.hashed_password
        )

        # 2. Hash new password
        hashed_password = get_password_hash(new_password)

        # 3. Update user in DB
        updated_user = await self.repo.update_user_by_id(
            target_user.id, {"hashed_password": hashed_password}
        )
        if not updated_user:
            return None
        logger.debug("Current user %s assigned with a new password", target_user)

        # 4. Update user cache
        if self.user_cache:
            await self.user_cache.set_user(
                target_user.id, UserDTO.from_orm(updated_user)
            )

        # 5. Get user contacts count
        contacts_count = await contacts_service.get_contacts_count(target_user.id)

        # 6. Return updated user DTO with contacts_count
        return UserWithStatsDTO.from_orm_with_count(updated_user, contacts_count)

    # TODO: admins may invoke email change, but can't change other user email directly
    # ? if email change reevaluate and decide if to change avatar based on a new email
    # ? or email change may invoke avatar change later, when the new email is confirmed
    # * Do not forget ot check for email exists conflict: _validate_email_conflict
    # TODO: admins may invoke password reset flow, but can't change other user password directly
    async def update_user_by_admin(
        self,
        requester: UserDTO,
        target_user_id: int,
        changes: Mapping[str, Any],
        contacts_service: ContactService,
    ) -> Optional[UserWithStatsDTO]:
        """
        Update user as admin/superadmin with role-based constraints.
        - Superadmin: can update any fields, including role.
        - Admin: can update users, but cannot update other admins or any role field.
            Admin may update own profile except role.
        """
        # 1. Check payload data

        if not changes:
            # Nothing to update
            raise BadProvidedDataError(
                {"Provided data": "No fields provided to update."}
            )

        # Email change is forbidden until proper email-change flow is implemented
        if "email" in changes:
            raise EmailChangeNotAllowedError(
                "Email change is temporarily disabled until the email change flow is implemented."
            )

        new_role: Optional[UserRole] = None
        if "role" in changes:
            # Check if role exists and valid
            try:
                new_role = UserService._validate_role_exists(changes["role"])
            except UserRoleIsInvalidError as exc:
                raise BadProvidedDataError(
                    {"role": f"Invalid role: {changes['role']}"}
                ) from exc
        new_username = changes.get("username", None)
        is_active = changes.get("is_active", NOT_PROVIDED)

        # 2. Fetch target user

        target_user_orm = await self.repo.get_user_by_id(target_user_id)
        if not target_user_orm:
            return None

        # 3. Convert orm to dto object
        target_user = UserDTO.from_orm(target_user_orm)

        # 4. Self-update is restricted - use current user update endpoint

        if requester.id == target_user.id:
            logger.warning(
                (
                    "Action is forbidden: %s attempted to perform self-update via admin endpoint "
                    "of the following fields %s"
                ),
                requester,
                changes.keys(),
            )
            raise UserRolePermissionError(
                (
                    "Self-update is not allowed via admin endpoint. "
                    "Use /me endpoint instead."
                )
            )

        # 5. Update of another user

        # 5.1 Requester - Target user role-based restrictions

        # Users and moderators cannot use admin update of other users
        if requester.role in {UserRole.USER, UserRole.MODERATOR}:
            raise UserRolePermissionError(
                f"{requester.role.value} are not allowed to update users"
            )

        # Admin cannot modify other admins
        if requester.role == UserRole.ADMIN and target_user.role == UserRole.ADMIN:
            raise UserRolePermissionError("Admins cannot modify other admins")

        # Non-superadmin cannot modify superadmin user data
        if (
            requester.role != UserRole.SUPERADMIN
            and target_user.role == UserRole.SUPERADMIN
        ):
            logger.warning(
                (
                    "Action is forbidden: Non-superadmin %s requested update of SUPERADMIN %s "
                    "of the following fields: %s"
                ),
                requester,
                target_user,
                changes.keys(),
            )
            raise UserRolePermissionError("Cannot modify superadmin user")

        # 5.2 Collect data to update

        data_to_update: Dict[str, Any] = {}
        changelog: Dict[str, str] = {}

        # Username
        if new_username and new_username != target_user.username:
            if requester.role != UserRole.SUPERADMIN:
                # Only superadmin can change usernames
                raise UserRolePermissionError(
                    f"{requester.role.value} cannot change usernames"
                )
            data_to_update["username"] = new_username
            changelog["username"] = f"Assigned new username={new_username}"

        # Role
        if new_role and new_role != target_user.role:
            if requester.role != UserRole.SUPERADMIN:
                # No other user than superadmin can perform role change
                logger.warning(
                    "Action is forbidden: Non-superadmin %s attempted to change role of %s %s",
                    requester,
                    target_user.role.value.upper(),
                    target_user,
                )
                raise UserRolePermissionError("Only superadmin can change user roles")
            elif (
                target_user.role == UserRole.SUPERADMIN
                and new_role != UserRole.SUPERADMIN
            ):
                # Superadmin can't level-down (downgrade) other superadmin role,
                # but still may lever-up (upgrade) it for other non-superadmin users
                logger.warning(
                    (
                        "Action is forbidden: "
                        "SUPERADMIN %s attempted to change other SUPERADMIN %s role to %s"
                    ),
                    requester,
                    target_user,
                    new_role.upper(),
                )
                raise UserRolePermissionError(
                    "Superadmin cannot change another superadmin's role"
                )
            else:
                data_to_update["role"] = new_role
                changelog["role"] = f"Assigned new role={new_role.value}"

        # Is active
        if is_active is not NOT_PROVIDED and is_active != target_user.is_active:
            data_to_update["is_active"] = is_active
            changelog["is_active"] = (
                f"User is {'activated' if is_active else 'deactivated'}"
            )

        # 5.3 Perform user update

        updated_user = await self.repo.update_user_by_id(target_user.id, data_to_update)
        if not updated_user:
            return None
        logger.debug(
            "%s %s updated other %s user %s with new data: %s",
            requester.role.value,
            requester,
            target_user.role.value,
            target_user,
            ", ".join([f"{k}:{v}" for k, v in changelog.items()]),
        )

        # 5.4 Update user cache
        if self.user_cache:
            await self.user_cache.set_user(
                target_user.id, UserDTO.from_orm(updated_user)
            )

        # 5.5 Get user contacts count
        contacts_count = await contacts_service.get_contacts_count(target_user.id)

        # 5.6 Return updated user DTO with contacts_count
        return UserWithStatsDTO.from_orm_with_count(updated_user, contacts_count)

    async def delete_user_by_admin(
        self,
        requester: UserDTO,
        target_user_id: int,
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

        user = await self.repo.get_user_by_id(target_user_id)
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

        logger.info(
            "%s %s deleted %s %s",
            requester.role.value.upper(),
            requester,
            deleted_user.role.value.upper(),
            UserDTO.from_orm(user),
        )

        # 6. Delete user cache
        if self.user_cache:
            await self.user_cache.invalidate_user(target_user_id)

        # 7. Return deleted user info with stats
        return UserWithStatsDTO.from_orm_with_count(
            deleted_user,
            contacts_count,
            hide_personal=True,
        )

    async def validate_user_credentials(
        self, username: str, plain_password: str
    ) -> UserDTO:
        """
        Validate user credentials and return user ID

        Raises:
        - InvalidUserCredentialsError: if any credential is not valid
        """
        user: Optional[UserDTO] = await self.get_user_by_username(username)
        if user is None:
            raise InvalidUserCredentialsError(f"User '{username}' does not exist")

        if not verify_password(plain_password, user.hashed_password):
            raise InvalidUserCredentialsError(
                f"Invalid password for the user '{username}'"
            )

        return user

    async def confirm_user_email(self, user_id: int, email: str) -> UserDTO:
        """
        Validate that the user exists, matches the token data, and confirm email.

        Raises:
            InvalidUserCredentialsError: if user not found or email doesn't match
            UserEmailIsAlreadyConfirmedError: if user email has been confirmed already
        """
        # Get user from db
        user_orm = await self.repo.get_user_by_id(user_id)
        if not user_orm:
            raise InvalidUserCredentialsError(
                f"User with provided user_id={user_id} not found"
            )

        # Convert to dto
        user = UserDTO.from_orm(user_orm)

        # Check if user is active before confirming
        if not user.is_active:
            logger.warning("Attempt to confirm email for inactive user %s", user)
            raise UserInactiveError("Cannot confirm email for inactive user")

        if user.email != email:
            raise InvalidUserCredentialsError(
                "Token email does not match current user email"
            )

        if user.is_email_confirmed:
            raise UserEmailIsAlreadyConfirmedError()

        updated_user_orm: Optional[User] = await self.repo.confirm_user_email_by_id(
            user_id
        )
        if not updated_user_orm:
            # happens only if someone confirmed email in parallel
            raise InvalidUserCredentialsError(
                f"Failed to confirm email for user_id={user_id}"
            )
        logger.info(
            "User email confirmed for user %s", UserDTO.from_orm(updated_user_orm)
        )

        updated_user_dto = UserDTO.from_orm(updated_user_orm)

        if self.user_cache:
            await self.user_cache.set_user(user_id, updated_user_dto)

        return updated_user_dto

    async def _create_user_common(
        self,
        creator: Optional[Union[UserDTO, AppInitActor]],
        username: str,
        email: str,
        password: str,
        role: UserRole,
        is_active: bool = True,
    ) -> UserDTO:
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

        # Resolve default avatar
        try:
            avatar_url = self.avatar_provider.resolve_default_avatar_or_none(email)
        except GravatarResolveError as exc:
            # best-effort:
            # Log and return None - indicates failed resolution, but still as valid domain value
            logger.debug("Failed to fetch Gravatar for email=%s: %s", email, exc)
            avatar_url = None

        # Normalize email
        normalized_email = email.strip().lower()

        # Create new user data
        new_user_data = {
            "username": username,
            "email": normalized_email,
            "hashed_password": hashed_password,
            "avatar": avatar_url,
            "is_active": is_active,
            "role": role,
            "is_email_confirmed": False,
        }
        new_user = await self.repo.create_user(new_user_data)

        creator_role = (
            f"{creator.role.value.upper()} "
            if creator and isinstance(creator, UserDTO)
            else ""
        )
        creator_info = creator if creator else "Anonymous user"
        new_user_info = UserDTO.from_orm(new_user)
        logger.info(
            "%s%s created a new %s %s",
            creator_role,
            creator_info,
            new_user_info.role,
            new_user_info,
        )

        return UserDTO.from_orm(new_user)

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
