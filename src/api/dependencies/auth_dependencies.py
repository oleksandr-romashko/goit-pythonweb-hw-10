"""FastAPI auth dependencies"""

from typing import TypeAlias, Any, Callable, Awaitable, Optional, Coroutine

from fastapi import Depends

from src.db.models.enums import UserRole
from src.services import UserService
from src.services.dtos import UserDTO
from src.utils.logger import logger

from src.utils.constants import (
    MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS,
    MESSAGE_ERROR_ACCESS_DENIED,
    MESSAGE_ERROR_INACTIVE_USER,
)

from src.api.errors import raise_http_401_error, raise_http_403_error

from .service_dependencies import get_user_service
from .token_dependencies import get_current_user_id


# === Custom dependency check type ===

Check: TypeAlias = Callable[[UserDTO], Awaitable[None]]
"""Validation check functions to be executed"""

# === Separate dependencies checks class ===


class Require:
    """Reusable declarative checks for validation."""

    @staticmethod
    def user_is_active() -> Check:
        """
        Ensure the current user is active.

        Raises:
            HTTPException (403): If the user is inactive (except SUPERADMIN).

        SUPERADMIN active status is ignored to prevent soft lock (SUPERADMIN is always active).
        """

        async def check(user: UserDTO) -> None:
            """Check ensures user has active status."""
            if not user.is_active and user.role != UserRole.SUPERADMIN:
                logger.warning(
                    (
                        "Deactivated user attempted to access protected resource: "
                        "user id = %s, username = %s"
                    ),
                    user.id,
                    user.username,
                )
                raise_http_403_error(MESSAGE_ERROR_INACTIVE_USER)

        return check

    @staticmethod
    def user_roles(*roles: UserRole) -> Check:
        """
        Ensure only certain user roles have access.

        Raises:
            HTTPException (403): If the user role in not within required roles.
        """

        async def check(user: UserDTO) -> None:
            """Check user role within allowed roles"""
            if user.role not in roles:
                logger.warning(
                    (
                        "User(id=%s, username=%s, role=%s) attempted to access protected resource "
                        "requiring one of [%s] roles"
                    ),
                    user.id,
                    user.username,
                    user.role,
                    ", ".join([role.value.upper() for role in roles]),
                )
                raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)

        return check


# === Factory for creating get_current_user_* dependency ===


def get_current_user_factory(
    *checks: Check,
) -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Factory to create current user dependency.

    Performs:
    - JWT authentication
    - User existence check
    - Adding of any additional provided optional checks

    Args:
        *checks: Optional async validation functions to be executed on the retrieved user.

    Returns:
        Dependency callable returning authenticated User instance.
    """

    async def dependency(
        user_id: int = Depends(get_current_user_id),
        user_service: UserService = Depends(get_user_service),
    ) -> UserDTO:
        """Dependency that returns the current user based on user ID obtained from JWT token."""

        # Get user DTO from the database
        user: Optional[UserDTO] = await user_service.get_user_by_id(user_id)

        # Check if users exists
        if user is None:
            logger.warning(
                "User not found for user_id=%s. Token is valid, but the user wasn't found.",
                user_id,
            )
            raise_http_401_error(MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS)

        # Call all other provided optional checks
        for check in checks:
            await check(user)

        logger.debug(
            (
                "User(id=%s, username=%s, role=%s, is_active=%s) "
                "authenticated successfully using valid access token."
            ),
            user.id,
            user.username,
            user.role,
            user.is_active,
        )

        return user

    return dependency


# === Alias dependencies for each user type and status, facilitating factory ===


def get_current_user() -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Dependency that returns the current user.

    Performs:
    - JWT authentication
    - User existence check

    Accessible for: all users (with any role and active status).
    """
    return get_current_user_factory()


def get_current_active_user() -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Dependency that returns the currently active user.

    Performs:
    - JWT authentication
    - Active status check (ignores SUPERADMIN deactivation)

    Accessible for: all active users (any role).
    """
    return get_current_user_factory(Require.user_is_active())


def get_current_active_moderator_user() -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Dependency that returns the current user with moderator-level access.

    Performs:
    - JWT authentication
    - Active status check
    - Role check: MODERATOR, ADMIN, or SUPERADMIN
    """
    return get_current_user_factory(
        Require.user_is_active(),
        Require.user_roles(UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN),
    )


def get_current_active_admin_user() -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Dependency that returns the current user with admin-level access.

    Performs:
    - JWT authentication
    - Active status check
    - Role check: ADMIN or SUPERADMIN
    """
    return get_current_user_factory(
        Require.user_is_active(),
        Require.user_roles(UserRole.ADMIN, UserRole.SUPERADMIN),
    )


def get_current_superadmin_user() -> Callable[..., Coroutine[Any, Any, UserDTO]]:
    """
    Dependency that returns the current SUPERADMIN user.

    Performs:
    - JWT authentication
    - Active status check
    - Role check: SUPERADMIN only
    """
    return get_current_user_factory(
        Require.user_is_active(),
        Require.user_roles(UserRole.SUPERADMIN),
    )


# TODO: Remove remained previous version of the refactored code
# ? Legacy: This code will be removed in the future as left as a reference only!
# * The code below is remained reference code, that has been used as a base
# * for the refactoring and obtaining current version of the code given above.
# * The main goal was to achieve flexibility with active status / roles / and
# * potentially other dependencies parameters.
# * Previous version was not so flexible and hard to expand.

# async def get_current_user(
#     user_id: int = Depends(get_current_user_id),
#     user_service: UserService = Depends(get_user_service),
# ) -> User:
#     """Retrieve current user by ID from JWT token."""
#     user = await user_service.get_user_by_id(user_id)
#     if user is None:
#         logger.warning(
#             "User not found for id=%s. Token is valid, but the user wasn't found.",
#             user_id,
#         )
#         raise_http_401_error(MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS)

#     logger.debug(
#         (
#             "User(id=%s, username=%s, role=%s, is_active=%s) "
#             "authenticated successfully using token."
#         ),
#         user.id,
#         user.username,
#         user.role,
#         user.is_active,
#     )

#     return user


# async def get_current_active_user(
#     user: User = Depends(get_current_user),
# ) -> User:
#     """Ensure the current user is active."""
#     if not user.is_active and user.role != UserRole.SUPERADMIN:
#         logger.warning(
#             "Deactivated user attempted to access protected resource: user id = %s, username = %s",
#             user.id,
#             user.username,
#         )
#         raise_http_403_error(MESSAGE_ERROR_INACTIVE_USER)

#     return user


# async def get_current_active_moderator_user(
#     user: User = Depends(get_current_active_user),
# ) -> User:
#     """Ensure current user is moderator or admin/superadmin."""
#     if user.role not in {UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN}:
#         logger.warning(
#             (
#                 "User attempted to access moderator protected resource: "
#                 "user_id=%s, username=%s"
#             ),
#             user.id,
#             user.username,
#         )
#         raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)
#     return user


# async def get_current_active_admin_user(
#     user: User = Depends(get_current_active_user),
# ) -> User:
#     """Ensure current user is admin or superadmin."""
#     if user.role not in {UserRole.ADMIN, UserRole.SUPERADMIN}:
#         logger.warning(
#             (
#                 "Non-admin user attempted to access admin protected resource: "
#                 "user_id=%s, username=%s"
#             ),
#             user.id,
#             user.username,
#         )
#         raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)
#     return user


# async def get_current_active_superadmin_user(
#     user: User = Depends(get_current_active_user),
# ) -> User:
#     """Ensure current user is superadmin."""
#     if user.role != UserRole.SUPERADMIN:
#         logger.warning(
#             (
#                 "Non-superadmin user attempted to access superadmin protected resource: "
#                 "user_id=%s, username=%s"
#             ),
#             user.id,
#             user.username,
#         )
#         raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)
#     return user
