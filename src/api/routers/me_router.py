"""
Users API endpoints.

Provides operations for users.
"""

from typing import Union

from fastapi import APIRouter, Depends, status, UploadFile, File, BackgroundTasks

from src.db.models.enums import UserRole
from src.services import (
    ContactService,
    FileService,
    UserService,
)
from src.services.dtos import UserDTO
from src.services.errors import (
    InvalidUserCredentialsError,
    BadProvidedDataError,
    FileUploadFailedError,
)
from src.services.validators.file_validator import (
    EmptyFileValidationError,
    TooLargeFileValidationError,
    UnsupportedMimeTypeValidationError,
    UnsupportedFileTypeValidationError,
)
from src.utils.logger import logger

from src.api.dependencies import (
    get_contacts_service,
    get_current_active_user,
    get_file_service,
    get_user_service,
)
from src.api.errors import (
    raise_http_400_error,
    raise_http_401_error,
    raise_http_403_error,
    raise_http_413_error,
    raise_http_415_error,
)
from src.api.extensions.rate_limiter import get_rate_limit, RateLimit
from src.api.responses.error_responses import (
    ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,
    ON_ME_PASSWORD_UPDATE_BAD_REQUEST,
    ON_AVATAR_UPLOAD_ERROR_RESPONSES,
)
from src.api.responses.success_responses import ON_ME_SUCCESS_RESPONSE
from src.api.schemas.users.requests import UserUpdatePasswordRequestSchema
from src.api.schemas.users.responses import (
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
    UserPasswordUpdateResponseSchema,
    UserAvatarUpdateResponseSchema,
)

# TODO: Add additional single action routes:
# * PATCH /me/email — solely email change (email change flow)
# TODO: Evaluate adding DELETE for /me or /me/delete — self-delete your account (anonymize data?)

router = APIRouter(
    prefix="/users/me",
    tags=["Current User / About Me self-service (User Access)"],
    responses={**ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES},
    dependencies=[Depends(get_rate_limit(RateLimit.ME))],
)


@router.get(
    "/",
    summary="Get information about the current user (Profile)",
    description=(
        "Information about the current user based on information "
        "obtained from JWT access token.\n\n"
        "No more than 10 requests per minute"
    ),
    response_model_exclude_none=True,
    responses={**ON_ME_SUCCESS_RESPONSE},
)
async def get_me(
    user: UserDTO = Depends(get_current_active_user()),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema]:
    """Return current user information."""
    response_data = UserAboutMeAdminResponseSchema.model_validate(user)

    # Add contacts count
    response_data.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Return full contact data for entrusted users
    if user.role in {UserRole.MODERATOR, UserRole.ADMIN, UserRole.SUPERADMIN}:
        return response_data

    # Sanitize some fields values for regular users
    response_data = _sanitize_response_non_entrusted(response_data)

    return UserAboutMeResponseSchema.model_validate(response_data)


@router.patch(
    "/password",
    summary="Update current user password",
    description=("Requires old password to confirm action authorization."),
    status_code=status.HTTP_200_OK,
    response_description="Successfully updated user password.",
    response_model=UserPasswordUpdateResponseSchema,
    responses={
        **ON_ME_PASSWORD_UPDATE_BAD_REQUEST,
    },
)
async def update_user_password(
    body: UserUpdatePasswordRequestSchema,
    user: UserDTO = Depends(get_current_active_user()),
    user_service: UserService = Depends(get_user_service),
) -> UserPasswordUpdateResponseSchema:
    """Update current user password."""
    current_password = body.current_password
    new_password = body.password

    # Validate input values (escape Pydantic sensitive data exposure)
    if current_password is None or new_password is None:
        errors = {}
        if current_password is None:
            errors["current_password"] = "This field is required."
        if new_password is None:
            errors["password"] = "This field is required."
        raise_http_400_error(
            detail={"errors": errors, "message": "Invalid request data."}
        )

    # Update password
    try:
        updated = await user_service.update_user_password(
            user, current_password, new_password
        )
    except BadProvidedDataError as exc:
        logger.info(exc)
        raise_http_400_error(detail=exc.errors)
    except InvalidUserCredentialsError as exc:
        raise_http_403_error(str(exc))

    # Edge case - user has been just deleted
    if updated is None:
        logger.warning(
            "User %s became inaccessible (removed or blocked) during/after update",
            user,
        )
        raise_http_401_error()

    # Return typical generalized response
    return UserPasswordUpdateResponseSchema()


@router.patch(
    "/avatar",
    summary="Upload or replace current user's avatar",
    description=(
        "Uploads a new avatar image for the authenticated user.\n\n"
        "- Avatar is uploaded to a storage\n"
        "- Avatar URL is updated in the user's profile\n"
        "- Old avatar is overwritten in cloud storage\n"
    ),
    response_model=UserAvatarUpdateResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully updated user avatar.",
    responses={**ON_AVATAR_UPLOAD_ERROR_RESPONSES},
)
async def update_user_avatar(
    file: UploadFile = File(),
    user: UserDTO = Depends(get_current_active_user()),
    file_service: FileService = Depends(get_file_service),
    user_service: UserService = Depends(get_user_service),
) -> UserAvatarUpdateResponseSchema:
    """Upload or replace current user's avatar."""
    # 1. Upload avatar file to storage
    try:
        upload_result = await file_service.upload_avatar(file, user)
    except UnsupportedMimeTypeValidationError as exc:
        raise_http_415_error(str(exc))
    except UnsupportedFileTypeValidationError as exc:
        raise_http_400_error(str(exc))
    except EmptyFileValidationError as exc:
        raise_http_400_error(str(exc))
    except TooLargeFileValidationError as exc:
        raise_http_413_error(str(exc))
    except FileUploadFailedError as exc:
        raise_http_400_error(str(exc))

    new_avatar_url = upload_result["url"]

    # 2. Update DB entry
    updated_user = await user_service.update_user_avatar(user, new_avatar_url)

    # Edge case - user deleted or became inaccessible during update
    if updated_user is None:
        logger.warning(
            "User %s became inaccessible during/after avatar update",
            user,
        )
        raise_http_401_error()

    # 3. Return new avatar URL
    return UserAvatarUpdateResponseSchema(avatar=new_avatar_url)


@router.patch(
    "/avatar/reset",
    summary="Reset user's avatar",
    description=(
        "Resets user's avatar to the Gravatar image (if available), "
        "or removes the avatar entirely (without servers fallback).\n\n"
        "- Determines Gravatar URL based on the user's email\n"
        "- Updates the user's avatar field in the database\n"
        "- Schedules deletion of the old avatar from storage\n"
    ),
    response_model=UserAvatarUpdateResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def reset_user_avatar(
    background_tasks: BackgroundTasks,
    user: UserDTO = Depends(get_current_active_user()),
    user_service: UserService = Depends(get_user_service),
    file_service: FileService = Depends(get_file_service),
) -> UserAvatarUpdateResponseSchema:
    """Reset user's avatar to Gravatar (or remove entirely)."""
    old_avatar_url = user.avatar

    # 1. Reset avatar value
    new_avatar_value = file_service.reset_avatar(user)

    # No avatar change (idempotent operation)
    if new_avatar_value == old_avatar_url:
        logger.debug(
            "%s requested avatar reset, but no change needed (avatar unchanged)", user
        )
        return UserAvatarUpdateResponseSchema(avatar=new_avatar_value)

    # 2. Update DB
    updated_user = await user_service.update_user_avatar(user, new_avatar_value)
    # Edge case: user deleted during operation
    if updated_user is None:
        logger.warning(
            "User %s became inaccessible during/after avatar reset",
            user,
        )
        raise_http_401_error()

    # 3. Remove old avatar in the background
    if not old_avatar_url:
        logger.debug("%s had no avatar to delete after avatar reset request", user)
    else:
        background_tasks.add_task(file_service.delete_avatar, user, old_avatar_url)

    return UserAvatarUpdateResponseSchema(avatar=new_avatar_value)


def _sanitize_response_non_entrusted(
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
