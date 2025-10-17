"""
Users API endpoints.

Provides operations for users.
"""

from typing import Union

from fastapi import APIRouter, Depends, status

from src.db.models import User
from src.db.models.enums import UserRole
from src.services import ContactService

from src.api.dependencies import get_current_active_user, get_contacts_service
from src.api.errors.error_responses import ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES
from src.api.schemas.users import (
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
    UserAboutMeOneOfResponseSchema,
)


router = APIRouter(
    prefix="/users/me",
    tags=["About Me / Current User (User Access)"],
    responses=ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,
)


@router.get(
    "/",
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    summary="Get information about the current user (About Me)",
    description=(
        "Information about the current user based on information "
        "obtained from JWT access token."
    ),
    response_description="Successfully retrieved current user information.",
    responses={
        200: {
            "description": "Regular User or Admin response",
            "model": UserAboutMeOneOfResponseSchema,
            "content": {
                "application/json": {
                    "examples": {
                        "Regular user": {
                            "summary": "Example for regular user",
                            "value": UserAboutMeResponseSchema.generate_example_recursive(),
                        },
                        "Admin user": {
                            "summary": "Example for admin user",
                            "value": UserAboutMeAdminResponseSchema.generate_example_recursive(),
                        },
                    }
                }
            },
        },
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
