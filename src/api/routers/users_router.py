"""
Users API endpoints.

Provides operations for users.
"""

from fastapi import APIRouter, Depends, status

from src.db.models import User
from src.services import UserService
from src.services.dtos import UserDTO
from src.services.errors import (
    UserConflictError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
)
from src.utils.constants import (
    MESSAGE_ERROR_USER_ROLE_IS_INVALID,
    MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS,
)

from src.api.dependencies import get_current_active_admin_user, get_user_service
from src.api.responses.error_responses import ON_CURRENT_ACTIVE_ADMIN_ERRORS_RESPONSES
from src.api.schemas.pagination import (
    PaginationFilterRequestSchema,
    PaginatedGenericResponseSchema,
)
from src.api.schemas.users.requests import (
    UserAdminCreateRequestSchema,
    UsersFilterRequestSchema,
)
from src.api.schemas.users.responses import UserAdminRegisteredUserResponseSchema
from src.api.errors import (
    raise_http_400_error,
    raise_http_403_error,
    raise_http_409_error,
)

router = APIRouter(
    prefix="/users",
    tags=["Users (Admin Access)"],
    responses={**ON_CURRENT_ACTIVE_ADMIN_ERRORS_RESPONSES},
)


@router.post(
    "/",
    summary="Create a new user (manual, admin access)",
    description=(
        "Create a new user manually. "
        "Accessible only for admin and superadmin users.\n\n"
        "- **Admin** can only create users with role '*User*'.\n"
        "- **Superadmin** can create users with roles '*User*' or '*Admin*'.\n"
        "- **Superadmin** role cannot be created via API.\n\n"
        "All fields are required except **avatar** (will try to set gravatar based on user email)"
        " and **is_active** (defaults to True)."
    ),
    response_model=UserAdminRegisteredUserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully created a new user.",
)
async def create_user_by_admin(
    body: UserAdminCreateRequestSchema,
    user: User = Depends(get_current_active_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> UserAdminRegisteredUserResponseSchema:
    """
    Create a new user by an admin or superadmin.

    Returns the created user info.
    """
    creator_dto = UserDTO.from_orm(user)
    try:
        new_user: User = await user_service.register_user_by_admin(
            creator=creator_dto,
            username=body.username,
            email=body.email,
            password=body.password,
            role_str=body.role,
            avatar=body.avatar,
            is_active=body.is_active,
        )
    except UserRoleIsInvalidError:
        raise_http_400_error(MESSAGE_ERROR_USER_ROLE_IS_INVALID)
    except UserRolePermissionError as exc:
        raise_http_403_error(
            f"{MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS}: {str(exc)}"
        )
    except UserConflictError as exc:
        raise_http_409_error(detail=exc.errors)

    return UserAdminRegisteredUserResponseSchema.model_validate(new_user)


@router.get(
    "/",
    summary="List all users",
    description=(
        "Retrieve a paginated list of users.\n\n"
        "Accessible only for admin and superadmin users.\n\n"
        "Optional query parameters `username`, `email`, `role`, and `active` "
        "perform **case-insensitive partial matches** "
        "(e.g. `username=ann` matches `Annette`).\n\n"
        "`skip`  and `limit` control pagination and always apply, "
        "whether or not filters are provided.\n"
        "- Pagination parameters: `limit`, `offset`.\n"
    ),
    response_model=PaginatedGenericResponseSchema[
        UserAdminRegisteredUserResponseSchema
    ],
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
    response_description="Successfully retrieved all users.",
)
async def get_all_users(
    pagination: PaginationFilterRequestSchema = Depends(),
    filters: UsersFilterRequestSchema = Depends(),
    user: User = Depends(get_current_active_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> PaginatedGenericResponseSchema[UserAdminRegisteredUserResponseSchema]:
    """
    Get a paginated list of users with optional filtration.

    Returns a list of users and pagination stats.
    Accessible only by admin and superadmin.
    """
    requester_dto = UserDTO.from_orm(user)
    users_dto, total_count = await user_service.get_all_users(
        requester_dto, pagination.model_dump(), filters.model_dump()
    )

    # Convert users DTOs to Pydantic schemas
    users_response = [
        UserAdminRegisteredUserResponseSchema.model_validate(dto.to_dict())
        for dto in users_dto
    ]

    return PaginatedGenericResponseSchema.model_validate(
        {
            "total": total_count,
            "skip": pagination.skip,
            "limit": pagination.limit,
            "data": users_response,
        }
    )
