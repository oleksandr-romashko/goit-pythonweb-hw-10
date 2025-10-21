"""FastAPI auth dependencies"""

from fastapi import Depends

from src.db.models import User
from src.db.models.enums import UserRole
from src.services import UserService
from src.utils.logger import logger

from src.utils.constants import (
    MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS,
    MESSAGE_ERROR_ACCESS_DENIED,
    MESSAGE_ERROR_INACTIVE_USER,
)

from src.api.errors import raise_http_401_error, raise_http_403_error

from .service_dependencies import get_user_service
from .token_dependencies import get_current_user_id


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """Retrieve current user by ID from JWT token."""
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        logger.warning(
            "User not found for id=%s. Token is valid, but the user wasn't found.",
            user_id,
        )
        raise_http_401_error(MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS)

    return user


async def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user is active."""
    if not user.is_active and user.role != UserRole.SUPERADMIN:
        logger.warning(
            "Deactivated user attempted to access protected resource: user id = %s, username = %s",
            user.id,
            user.username,
        )
        raise_http_403_error(MESSAGE_ERROR_INACTIVE_USER)

    return user


async def get_current_active_admin_user(
    user: User = Depends(get_current_active_user),
) -> User:
    """Ensure current user is admin or superadmin."""
    if user.role not in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        logger.warning(
            (
                "Non-admin user attempted to access admin protected resource: "
                "user id = %s, username = %s"
            ),
            user.id,
            user.username,
        )
        raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)
    return user


async def get_current_superadmin_user(
    user: User = Depends(get_current_active_user),
) -> User:
    """Ensure current user is superadmin."""
    if user.role != UserRole.SUPERADMIN:
        logger.warning(
            (
                "Non-superadmin user attempted to access superadmin protected resource: "
                "user id = %s, username = %s"
            ),
            user.id,
            user.username,
        )
        raise_http_403_error(MESSAGE_ERROR_ACCESS_DENIED)
    return user
