"""Service layer providing business logic for managing User entities."""

from dataclasses import dataclass
from typing import Optional, Union, Any, Mapping, Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.models.enums.user_roles import UserRole
from src.db.repository import UsersRepository
from src.providers.avatar_provider import GravatarProvider
from src.providers.cache_providers.logs import CacheEvent
from src.providers.cache_providers.user_cache import UserRedisCacheProvider
from src.providers.errors import GravatarResolveError
from src.utils.constants import DEFAULT_SUPERADMIN_EMAIL, DEFAULT_SUPERADMIN_PASSWORD
from src.utils.logger import logger
from src.utils.query_helpers import get_pagination
from src.utils.security.password_utils import get_password_hash, verify_password

from .dtos import UserDTO, UserWithStatsDTO
from .errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    UserConflictError,
    UserInactiveError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
    UserEmailIsAlreadyConfirmedError,
)
from .markers import AppInitActor, APP_INIT_ACTOR, NOT_PROVIDED


@dataclass
class UserGetResult:
    """Dataclass representing retrieving user result"""

    user: UserDTO
    show_full: bool


@dataclass
class UserAdminUpdateResult:
    """Dataclass representing user update result"""

    user: UserDTO
    avatar_reset: bool
    old_avatar: Optional[str]


@dataclass
class UserAdminDeleteResult:
    """Dataclass representing user deletion result"""

    user: UserDTO
    avatar: Optional[str]


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
    """
    Handles business logic related to users.

    UserService caching policy:
    - User cache is keyed based on user_id
    - Cache is updated on all write paths
    - Read paths may optionally warm the cache
    """

    def __init__(
        self,
        db_session: AsyncSession,
        *,
        repo: Optional[UsersRepository] = None,
        avatar_provider: Optional[GravatarProvider] = None,
        user_cache: Optional[UserRedisCacheProvider] = None,
    ) -> None:
        """Initialize the service with a users repository and other dependencies."""
        self.repo = repo or UsersRepository(db_session)
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
        """
        Create a superuser if it doesn't exist. Returns True if created.

        Provided with user caching via _create_user_common, if user cache is available.
        """
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

        Provided with user caching via _create_user_common, if user cache is available.

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
        is_active: Optional[bool] = None,
    ) -> UserDTO:
        """
        Create a new user by an admin or superadmin.

        Provided with user caching via _create_user_common, if user cache is available.
        """

        # Provided role check
        # Check if role exists and valid
        try:
            role = UserService._validate_role_exists(role_str)
        except UserRoleIsInvalidError as exc:
            raise BadProvidedDataError({"role": f"Invalid role: {role_str}"}) from exc

        # Role restriction logic check
        self._validate_creation_permissions(creator, role, username, email)

        # Create user in DB and get user user data
        return await self._create_user_common(
            creator=creator,
            username=username,
            email=email,
            password=password,
            role=role,
            is_active=is_active if is_active is not None else True,
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
                requester.role == UserRole.SUPERADMIN  # Superadmin sees everyone fully
                or user.id == requester.id  # User sees self fully
                or user.role in {UserRole.MODERATOR, UserRole.USER}
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
        """
        Retrieve a user dto by ID or return None if not exists.

        Provided with user caching (read/write), if user cache is available.
        """
        # 1. Try get user from cache
        if self.user_cache:
            cashed = await self.user_cache.get_user(user_id)
            if cashed is not None:
                CacheEvent.log_user_cache_hit(user_id)
                return cashed
            CacheEvent.log_user_cache_miss(user_id)
        else:
            CacheEvent.log_user_cache_skipped()

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
    ) -> Optional[UserGetResult]:
        """
        Retrieve a single user by ID.

        - SUPERADMIN can see any user.
        - ADMIN cannot see other inactive admins.
        - Contact counts are hidden for admins viewing other admins.
        """
        user_orm = await self.repo.get_user_by_id(user_id)
        if not user_orm:
            return None

        user = UserDTO.from_orm(user_orm)

        # Restrict providing superadmin data
        if user.role == UserRole.SUPERADMIN and requester.id != user.id:
            logger.warning(
                "Action is forbidden: %s %s attempted to view info about SUPERADMIN user %s",
                requester.role.upper(),
                requester,
                user,
            )
            return None

        # Define if to show full user information
        show_full = (
            requester.role == UserRole.SUPERADMIN
            or requester.id == user.id
            or user.role in {UserRole.MODERATOR, UserRole.USER}
        )

        return UserGetResult(user=user, show_full=show_full)

    async def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """
        Retrieve a user by username or return None if not exists.

        Provided with warming cache on user, if user cache is available.
        """
        user_orm = await self.repo.get_user_by_username(username)
        if not user_orm:
            return None

        user_dto = UserDTO.from_orm(user_orm)

        # Update user cache (warming cache)
        if self.user_cache:
            await self.user_cache.set_user(user_dto.id, user_dto)

        return user_dto

    async def get_user_by_email(self, email: str) -> Optional[UserDTO]:
        """
        Retrieve a user by email or return None if not exists.

        Provided with warming cache on user, if user cache is available.
        """
        user_orm: Optional[User] = await self.repo.get_user_by_email(email)
        if not user_orm:
            return None

        user_dto = UserDTO.from_orm(user_orm)

        # Update user cache (warming cache)
        if self.user_cache:
            await self.user_cache.set_user(user_dto.id, user_dto)

        return user_dto

    async def update_user_avatar(
        self,
        target_user: UserDTO,
        new_avatar_value: Optional[str],
    ) -> Optional[str]:
        """
        Update current user avatar value in DB.

        Updates user cache, if user cache is available.

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
    ) -> Optional[UserDTO]:
        """
        Update a current user password.

        Updates user cache, if user cache is available.

        Raises:
        - BadProvidedDataError: if any field has bad or improper value
        - InvalidUserCredentialsError: if old password is not correct or doesn't match
        """
        # 1. Validate password change
        UserService._validate_password_change(
            current_password, new_password, target_user.hashed_password
        )

        # 2. Hash new password
        hashed_password = get_password_hash(new_password)

        # 3. Update user in DB
        user_orm = await self.repo.update_user_by_id(
            target_user.id, {"hashed_password": hashed_password}
        )
        if not user_orm:
            return None

        logger.debug("User %s updated password", target_user)

        user_dto = UserDTO.from_orm(user_orm)

        # 4. Update user cache
        if self.user_cache:
            await self.user_cache.set_user(target_user.id, user_dto)

        # 5. Return updated user DTO
        return user_dto

    async def update_user_by_admin(
        self,
        requester: UserDTO,
        target_user_id: int,
        payload: Mapping[str, Any],
    ) -> Optional[UserAdminUpdateResult]:
        """
        Update user as admin/superadmin with role-based constraints.
        - Nobody can perform self-update via this method.
        - Superadmin: can update any fields, including role.
        - Nobody can update other superadmin users.
        - Admin: can update users, but cannot update other admins or any role field.

        Updates user cache, if user cache is available.
        """
        # 1. Check payload data

        if not payload:
            # Nothing to update
            raise BadProvidedDataError(
                {"Provided data": "No fields provided to update."}
            )

        # role
        new_role: Optional[UserRole] = None
        if "role" in payload:
            # Check if role exists and valid
            try:
                new_role = UserService._validate_role_exists(payload["role"])
            except UserRoleIsInvalidError as exc:
                raise BadProvidedDataError(
                    {"role": f"Invalid role: {payload['role']}"}
                ) from exc
        new_username = payload.get("username", None)
        is_active = payload.get("is_active", NOT_PROVIDED)

        # avatar
        avatar = payload["avatar"] if "avatar" in payload else NOT_PROVIDED
        if avatar is not NOT_PROVIDED and avatar is not None:
            raise BadProvidedDataError(
                {
                    "avatar": (
                        f"Invalid optional avatar field value: {payload['avatar']}. "
                        "Only null value is allowed."
                    )
                }
            )

        # 2. Fetch target user

        target_user_orm = await self.repo.get_user_by_id(target_user_id)
        if not target_user_orm:
            return None

        # 3. Convert orm to dto object
        target_user = UserDTO.from_orm(target_user_orm)

        # 4. Restrictions for update

        # Self-update is restricted - use current user update endpoint
        if requester.id == target_user.id:
            logger.warning(
                (
                    "Action is forbidden: %s attempted to perform self-update via admin endpoint "
                    "of the following fields %s"
                ),
                requester,
                payload.keys(),
            )
            raise UserRolePermissionError(
                (
                    "Self-update is not allowed via admin endpoint. "
                    "Use /me endpoint instead."
                )
            )

        # 5. Update of another user

        # 5.1 Requester - Target user role-based restrictions

        # Prevent updating superadmin data
        if target_user_orm.role == UserRole.SUPERADMIN:
            logger.warning(
                "Action is forbidden: %s %s attempted to update SUPERADMIN %s",
                requester.role.upper(),
                requester,
                target_user,
            )
            raise UserRolePermissionError("Update of superadmin user is not allowed.")

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
                payload.keys(),
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
                    f"{requester.role.upper()} cannot change usernames"
                )
            data_to_update["username"] = new_username
            changelog["username"] = f"Assigned new username = '{new_username}'"

        # Role
        if new_role and new_role != target_user.role:
            if requester.role != UserRole.SUPERADMIN:
                # No other user than superadmin can perform role change
                logger.warning(
                    "Action is forbidden: Non-superadmin %s attempted to change role of %s %s",
                    requester,
                    target_user.role.upper(),
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
                changelog["role"] = f"Assigned new role = '{new_role.upper()}'"

        # Is active
        if is_active is not NOT_PROVIDED and is_active != target_user.is_active:
            data_to_update["is_active"] = is_active
            changelog["is_active"] = (
                f"User is {'activated' if is_active else 'deactivated'}"
            )

        # Avatar
        new_avatar = target_user.avatar
        if avatar is not NOT_PROVIDED and avatar is None:
            # reset user avatar
            new_avatar = self.avatar_provider.resolve_default_avatar_or_none(
                target_user.email
            )
            if target_user.avatar != new_avatar:
                data_to_update["avatar"] = new_avatar
                changelog["avatar"] = "Performed user avatar reset"

        # 5.3 Perform user update

        result_user_orm = None
        if not data_to_update:
            # Nothing to update
            logger.debug(
                (
                    "%s %s tried to update other %s %s with the same user data as it had already. "
                    "No changes in user data. Actual update skipped."
                ),
                requester.role.upper(),
                requester,
                target_user.role.upper(),
                target_user,
            )
            result_user_orm = target_user_orm
        else:
            result_user_orm = await self.repo.update_user_by_id(
                target_user.id, data_to_update
            )
            if not result_user_orm:
                return None

            logger.debug(
                "%s %s updated other %s %s with new data: %s.",
                requester.role.upper(),
                requester,
                target_user.role.upper(),
                target_user,
                "; ".join([f"{k.upper()}: {v}" for k, v in changelog.items()]),
            )

            # 5.4 Update user cache
            if self.user_cache:
                await self.user_cache.set_user(
                    target_user.id, UserDTO.from_orm(result_user_orm)
                )

        # 5.5 Form reply
        user_dto = UserDTO.from_orm(result_user_orm)
        avatar_reset = (
            avatar is not NOT_PROVIDED
            and avatar is None
            and target_user.avatar is not None
            and target_user.avatar != new_avatar
        )
        old_avatar = target_user.avatar if avatar_reset else None
        return UserAdminUpdateResult(
            user=user_dto,
            avatar_reset=avatar_reset,
            old_avatar=old_avatar,
        )

    async def delete_user_by_admin(
        self,
        requester: UserDTO,
        target_user_id: int,
    ) -> Optional[UserAdminDeleteResult]:
        """
        Delete a user by admin or superadmin, with strict role-based rules.

        Rules:
        - SUPERADMIN can delete any user except themselves and other SUPERADMINs.
        - ADMIN can delete only regular USERs, not themselves or other admins.
        - MODERATOR or USER cannot delete anyone.

        Invalidates user cache, if user cache is available.

        Raises:
            UserRolePermissionError: if requester is not allowed to delete the target user.
        """
        # 1. Fetch the target user

        user_orm = await self.repo.get_user_by_id(target_user_id)
        if not user_orm:
            return None

        # 2. Prevent self-deletion

        if requester.id == user_orm.id:
            raise UserRolePermissionError("Users cannot delete themselves")

        # 3. Role-based restrictions

        # 3.1 User cannot delete anyone
        if requester.role == UserRole.USER:
            raise UserRolePermissionError("Users are not allowed to delete users")

        # 3.2 Moderator cannot delete anyone
        if requester.role == UserRole.MODERATOR:
            raise UserRolePermissionError("Moderators are not allowed to delete users")

        # 3.3 Admin cannot delete other admins or superadmins
        if requester.role == UserRole.ADMIN and user_orm.role in {
            UserRole.ADMIN,
            UserRole.SUPERADMIN,
        }:
            raise UserRolePermissionError("Admins cannot delete admins")

        # 3.4 Superadmin cannot delete other superadmins
        if (
            requester.role == UserRole.SUPERADMIN
            and user_orm.role == UserRole.SUPERADMIN
        ):
            raise UserRolePermissionError("Superadmin cannot delete another superadmin")

        # 4. Perform deletion

        avatar = user_orm.avatar

        deleted = await self.repo.remove_user_by_id(user_orm.id)
        if not deleted:
            return None

        logger.info(
            "%s %s deleted %s %s",
            requester.role.upper(),
            requester,
            deleted.role.upper(),
            UserDTO.from_orm(deleted),
        )

        # 5. Invalidate deleted user cache
        if self.user_cache:
            await self.user_cache.invalidate_user(target_user_id)

        return UserAdminDeleteResult(UserDTO.from_orm(deleted), avatar)

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

        Updates user cache, if user cache is available.

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
        """
        Common internal method for user creation logic.

        Updates user cache, if user cache is available.
        """

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

        # Create new user
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
        new_user_dto = UserDTO.from_orm(new_user)

        # Log creation
        creator_role = (
            f"{creator.role.upper()} "
            if creator and isinstance(creator, UserDTO)
            else ""
        )
        creator_info = creator if creator else "Anonymous user"
        logger.info(
            "%s%s created a new %s %s",
            creator_role,
            creator_info,
            new_user_dto.role.upper(),
            new_user_dto,
        )

        # Set cache for created user
        if self.user_cache:
            await self.user_cache.set_user(new_user_dto.id, new_user_dto)

        return new_user_dto

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
