"""
Users API endpoints.

Provides operations for users.
"""

from fastapi import APIRouter, Depends, status

from src.services import UserService, ContactService
from src.services.dtos import UserDTO
from src.services.errors import (
    UserConflictError,
    EmailChangeNotAllowedError,
    BadProvidedDataError,
    UserRolePermissionError,
    UserViewPermissionError,
)
from src.utils.constants import (
    MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS,
    MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED,
    MESSAGE_ERROR_EMAIL_CHANGE_IS_FORBIDDEN,
)
from src.utils.logger import logger

from src.api.dependencies import (
    get_current_active_admin_user,
    get_user_service,
    get_contacts_service,
)
from src.api.responses.error_responses import (
    ON_CURRENT_ACTIVE_ADMIN_ERRORS_RESPONSES,
    ON_USER_FORBIDDEN_OR_ROLE_IS_INVALID_RESPONSE,
    ON_UPDATE_EMPTY_BAD_REQUEST_RESPONSE,
    ON_USER_NOT_FOUND_OR_VIEW_RESTRICTED_RESPONSE,
    ON_USER_NOT_FOUND_OR_DELETE_RESTRICTED_RESPONSE,
)
from src.api.responses.success_responses import ON_GET_USER_BY_ID_SUCCESS_RESPONSE
from src.api.schemas.pagination import (
    PaginationFilterRequestSchema,
    PaginatedGenericResponseSchema,
)
from src.api.schemas.users.requests import (
    UserAdminCreateRequestSchema,
    UsersFilterRequestSchema,
    UserUpdateAdminRequestSchema,
)
from src.api.schemas.users.responses import UserAdminRegisteredUserResponseSchema
from src.api.errors import (
    raise_http_400_error,
    raise_http_403_error,
    raise_http_404_error,
    raise_http_409_error,
)

router = APIRouter(
    prefix="/users",
    tags=["Users (Admin Access)"],
    responses={**ON_CURRENT_ACTIVE_ADMIN_ERRORS_RESPONSES},
)


# TODO: PATCH /users/{id}/* — separate simple endpoints to edit user:
# * role, active status, block, etc.


@router.post(
    "/",
    summary="Create a new user",
    description=(
        "🔒 **Access restricted:** Admin and Superadmin only.\n\n"
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
    user: UserDTO = Depends(get_current_active_admin_user()),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> UserAdminRegisteredUserResponseSchema:
    """
    Create a new user by an admin or superadmin.

    Accessible only by admin and superadmin.
    Returns the created user info.
    """
    try:
        new_user: UserDTO = await user_service.register_user_by_admin(
            creator=user,
            username=body.username,
            email=body.email,
            password=body.password,
            role_str=body.role,
            is_active=body.is_active,
        )
    except BadProvidedDataError as exc:
        raise_http_400_error(detail=exc.errors)
    except UserRolePermissionError as exc:
        raise_http_403_error(
            f"{MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS}: {str(exc)}"
        )
    except UserConflictError as exc:
        raise_http_409_error(detail=exc.errors)

    response_data = UserAdminRegisteredUserResponseSchema.model_validate(new_user)

    # Add contacts count (probably zero for a newly created user)
    response_data.contacts_count = await contacts_service.get_contacts_count(user.id)

    return response_data


@router.get(
    "/",
    summary="List all users",
    description=(
        "Retrieve a paginated list of users.\n\n"
        "🔒 **Access restricted:** Admin and Superadmin only.\n\n"
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
    user: UserDTO = Depends(get_current_active_admin_user()),
    user_service: UserService = Depends(get_user_service),
) -> PaginatedGenericResponseSchema[UserAdminRegisteredUserResponseSchema]:
    """
    Get a paginated list of users with optional filtration.

    Accessible only by admin and superadmin.
    Returns a list of users and pagination stats.
    """
    users_dto, total_count = await user_service.get_all_users(
        user, pagination.model_dump(), filters.model_dump()
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


@router.get(
    "/{user_id}",
    summary="Get user details by ID",
    description=(
        "Retrieve details of a specific user by their ID.\n\n"
        "🔒 **Access restricted:** Admin and Superadmin only.\n\n"
        "- **Superadmin** can see any user.\n"
        "- **Admin** can see other users and admins, but cannot see other inactive admins.\n"
    ),
    status_code=status.HTTP_200_OK,
    response_model_exclude_none=True,
    response_description="Successfully retrieved user details.",
    responses={
        **ON_GET_USER_BY_ID_SUCCESS_RESPONSE,
        **ON_USER_NOT_FOUND_OR_VIEW_RESTRICTED_RESPONSE,
    },
)
async def get_user_by_id(
    user_id: int,
    user: UserDTO = Depends(get_current_active_admin_user()),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> UserAdminRegisteredUserResponseSchema:
    """
    Get a specific user by ID.

    Accessible only by admin and superadmin.
    Returns the created user info.
    """
    try:
        user_dto = await user_service.get_user_by_id_for_admin(
            requester=user, user_id=user_id, contacts_service=contacts_service
        )
    except UserViewPermissionError:
        raise_http_404_error(MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED)

    if not user_dto:
        raise_http_404_error(MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED)

    return UserAdminRegisteredUserResponseSchema.model_validate(user_dto.to_dict())


@router.patch(
    "/{user_id}",
    summary="Partially update user",
    description=(
        "Partially update existing user record by id.\n\n"
        "🔒 **Access restricted:** Admin and Superadmin only.\n\n"
        "- **Superadmin**: may update any user and roles.\n"
        "- **Admin**: may update regular users (and optionally own profile), "
        "**but NOT** other admins' roles or other admins at all.\n"
        "- **Only Superadmin** may change roles.\n"
        "- **No one** may change their own role.\n"
    ),
    status_code=status.HTTP_200_OK,
    response_model=UserAdminRegisteredUserResponseSchema,
    response_model_exclude_none=True,
    responses={
        **ON_USER_FORBIDDEN_OR_ROLE_IS_INVALID_RESPONSE,
        **ON_UPDATE_EMPTY_BAD_REQUEST_RESPONSE,
        **ON_USER_NOT_FOUND_OR_VIEW_RESTRICTED_RESPONSE,
    },
)
async def update_user(
    user_id: int,
    body: UserUpdateAdminRequestSchema,
    user: UserDTO = Depends(get_current_active_admin_user()),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> UserAdminRegisteredUserResponseSchema:
    """
    Update a specific user by ID.

    Accessible only by admin and superadmin.
    Returns the updated user info.
    """
    update_payload = body.model_dump(exclude_unset=True)

    try:
        updated_dto = await user_service.update_user_by_admin(
            requester=user,
            target_user_id=user_id,
            changes=update_payload,
            contacts_service=contacts_service,
        )
    except EmailChangeNotAllowedError as exc:
        logger.info(exc)
        raise_http_403_error(MESSAGE_ERROR_EMAIL_CHANGE_IS_FORBIDDEN)
    except UserRolePermissionError as exc:
        raise_http_403_error(
            f"{MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS}: {str(exc)}"
        )
    except UserViewPermissionError:
        raise_http_404_error(MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED)

    if not updated_dto:
        raise_http_404_error(MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED)

    return UserAdminRegisteredUserResponseSchema.model_validate(updated_dto.to_dict())


@router.delete(
    "/{user_id}",
    summary="Delete a user",
    description=(
        "Delete an existing user by their ID.\n\n"
        "🔒 **Access restricted:** Admin and Superadmin only.\n\n"
        "- **Superadmin** can delete any user except themselves and other superadmins.\n"
        "- **Admin** can delete only regular users (not themselves, not other admins "
        "or superadmins).\n"
        "- **Users** cannot delete anyone.\n\n"
        "⚠️ The operation performs a **permanent deletion** (not soft delete)."
    ),
    status_code=status.HTTP_200_OK,
    response_model=UserAdminRegisteredUserResponseSchema,
    response_model_exclude_none=True,
    response_description="Successfully deleted the user.",
    responses={
        **ON_USER_FORBIDDEN_OR_ROLE_IS_INVALID_RESPONSE,
        **ON_USER_NOT_FOUND_OR_DELETE_RESTRICTED_RESPONSE,
    },
)
async def delete_user(
    user_id: int,
    user: UserDTO = Depends(get_current_active_admin_user()),
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> UserAdminRegisteredUserResponseSchema:
    """
    Delete a specific user by ID.

    Accessible only by admin and superadmin.

    Returns the deleted user's data (for confirmation/logging purposes).
    """
    try:
        deleted_dto = await user_service.delete_user_by_admin(
            requester=user,
            target_user_id=user_id,
            contacts_service=contacts_service,
        )
    except UserRolePermissionError as exc:
        raise_http_403_error(
            f"{MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS}: {str(exc)}"
        )

    if not deleted_dto:
        raise_http_404_error(MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED)

    return UserAdminRegisteredUserResponseSchema.model_validate(deleted_dto.to_dict())
