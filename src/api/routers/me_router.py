"""
Users API endpoints.

Provides operations for users.
"""

from typing import Optional, Union

from fastapi import APIRouter, Depends, status

from src.db.models import User
from src.db.models.enums import UserRole
from src.services import UserService, ContactService
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
from src.api.responses.error_responses import ON_BAD_REQUEST_RESPONSE
from src.api.responses.success_responses import ON_ME_SUCCESS_RESPONSE
from src.api.schemas.users.requests import UserUpdateRequestSchema
from src.api.schemas.users.responses import (
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
)

# TODO: DELETE /me — видалити свій акаунт (якщо ти це дозволяєш)
# TODO: Можна додати дрібніші ендпоінти:
# TODO:     PATCH /me/password — зміна пароля
# TODO:     PATCH /me/avatar — зміна аватара
# TODO:     PATCH /me/email — оновлення email з підтвердженням

router = APIRouter(
    prefix="/users/me",
    tags=["Current User / About Me (User Access)"],
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
    data = UserAboutMeAdminResponseSchema.model_validate(user)

    # Add number of user contacts
    data.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Return full contact data for admin users
    if user.role in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        return data

    # For non-admin users - sanitize some fields values by setting them to None
    data.role = None
    data.created_at = None
    data.updated_at = None

    return UserAboutMeResponseSchema.model_validate(data)


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
    responses={**ON_ME_SUCCESS_RESPONSE, **ON_BAD_REQUEST_RESPONSE},
)
async def update_me(
    body: UserUpdateRequestSchema,
    user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema]:
    """Partially update current user information."""
    try:
        orm_user: Optional[User] = await user_service.update_user(
            user, **body.model_dump()
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
    if orm_user is None:
        raise_http_401_error("User not authenticated or removed")

    response = UserAboutMeAdminResponseSchema.model_validate(orm_user)

    # Add number of user contacts to the response
    response.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Return full contact data for admin users
    if user.role in {UserRole.ADMIN, UserRole.SUPERADMIN}:
        return response

    # For non-admin users - sanitize some fields values by setting them to None
    response.role = None
    response.created_at = None
    response.updated_at = None

    return UserAboutMeResponseSchema.model_validate(response)
