"""
Users API endpoints.

Provides operations for users.
"""

from typing import Union

from fastapi import APIRouter, Depends

from src.db.models import User
from src.db.models.enums import UserRole
from src.services import ContactService

from src.api.dependencies import (
    get_current_active_user,
    get_contacts_service,
)
from src.api.responses.error_responses import ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES
from src.api.responses.success import ON_ME_SUCCESS_RESPONSE
from src.api.schemas.users.responses import (
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
)

router = APIRouter(
    prefix="/users/me",
    tags=["Current User / About Me (User Access)"],
    responses={
        **ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,
    },
)


@router.get(
    "/",
    summary="Get information about the current user (Profile)",
    description=(
        "Information about the current user based on information "
        "obtained from JWT access token."
    ),
    response_model_exclude_none=True,
    responses={
        **ON_ME_SUCCESS_RESPONSE,
    },
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
