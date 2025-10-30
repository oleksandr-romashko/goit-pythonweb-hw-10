"""
Users API endpoints.

Provides operations for users.
"""

from typing import Optional, Union

from fastapi import APIRouter, Depends, status

from src.db.models import User
from src.db.models.enums import UserRole
from src.services import UserService, ContactService
from src.services.dtos import UserDTO, UserWithStatsDTO
from src.services.errors import (
    InvalidUserCredentialsError,
    BadProvidedDataError,
    UserConflictError,
)
from src.utils.logger import logger

from src.api.dependencies import (
    get_current_active_user,
    get_user_service,
    get_contacts_service,
)
from src.api.errors import (
    raise_http_400_error,
    raise_http_401_error,
    raise_http_403_error,
    raise_http_409_error,
)
from src.api.responses.error_responses import ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES
from src.api.responses.error_responses import (
    ON_ME_UPDATE_BAD_REQUEST_RESPONSE_EMPTY_AND_BAD_VALUES,
)
from src.api.responses.success_responses import ON_ME_SUCCESS_RESPONSE
from src.api.schemas.users.requests import UserUpdateRequestSchema
from src.api.schemas.users.responses import (
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
)

# TODO: Add additional single action routes:
# * PATCH /me/password — solely password change
# * PATCH /me/avatar — solely avatar change
# * PATCH /me/email — solely email change
# TODO: Evaluate adding DELETE for /me or /me/delete — self-delete your account (anonymize data?)

router = APIRouter(
    prefix="/users/me",
    tags=["Current User / About Me self-service (User Access)"],
    responses={**ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES},
)


@router.get(
    "/",
    summary="Get information about the current user (Profile)",
    description=(
        "Information about the current user based on information "
        "obtained from JWT access token."
    ),
    response_model_exclude_none=True,
    responses={**ON_ME_SUCCESS_RESPONSE},
)
async def get_me(
    user: User = Depends(get_current_active_user),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema]:
    """Return current user information."""
    response_data = UserAboutMeAdminResponseSchema.model_validate(user)

    # Add contacts count
    response_data.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Return full contact data for admin users
    if user.role in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        return response_data

    # Sanitize some fields values for non-admin users
    response_data = _sanitize_non_admin_response(response_data)

    return UserAboutMeResponseSchema.model_validate(response_data)


@router.patch(
    "/",
    summary="Update current user information (partial update)",
    description=(
        "Update only some provided fields of the current user.\n\n<br>"
        "All fields are optional, but at least one field should be provided."
    ),
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
    response_description="Successfully updated user contact.",
    responses={
        **ON_ME_SUCCESS_RESPONSE,
        **ON_ME_UPDATE_BAD_REQUEST_RESPONSE_EMPTY_AND_BAD_VALUES,
    },
)
async def update_me(
    body: UserUpdateRequestSchema,
    user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema]:
    """Partially update current user information."""
    try:
        updated_user_dto: Optional[UserWithStatsDTO] = (
            await user_service.update_current_user(
                UserDTO.from_orm(user), **body.model_dump()
            )
        )
    except InvalidUserCredentialsError as exc:
        raise_http_403_error(str(exc))
    except BadProvidedDataError as exc:
        logger.info(exc)
        raise_http_400_error(detail=exc.errors)
    except UserConflictError as exc:
        logger.info(exc)
        raise_http_409_error(detail=exc.errors)

    # Edge case - user has been just deleted
    if updated_user_dto is None:
        raise_http_401_error("User not authenticated or removed")

    response_data = UserAboutMeAdminResponseSchema.model_validate(
        updated_user_dto.to_dict()
    )

    # Add number of user contacts to the response
    response_data.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Return full contact data for admin users
    if user.role in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        return response_data

    # Sanitize some fields values for non-admin users
    response_data = _sanitize_non_admin_response(response_data)

    return UserAboutMeResponseSchema.model_validate(response_data)


def _sanitize_non_admin_response(
    data: UserAboutMeAdminResponseSchema,
) -> UserAboutMeAdminResponseSchema:
    """
    Hide some fields values for non-admin users by setting them to None

    This will allow for sensitive data not to be shown in the response
    """
    data.role = None
    data.created_at = None
    data.updated_at = None

    return data
