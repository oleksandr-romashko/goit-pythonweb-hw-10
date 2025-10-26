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
from src.api.schemas.users.requests import UserAdminCreateRequestSchema
from src.api.schemas.users.responses import UserAdminCreatedUserResponseSchema
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


# TODO:	GET /users	Отримати список користувачів з фільтрацією та пагінацією	Admin / Superadmin
# TODO:	GET /users/{user_id}	Отримати деталі конкретного користувача	Admin / Superadmin
# TODO:	PATCH /users/{user_id}	Часткове оновлення користувача (роль, статус, email тощо)	Superadmin (роль), Admin (решта)
# TODO:	DELETE /users/{id}	Видалити користувача	Admin / Superadmin
# TODO: (optional) PATCH /users/{id}/role Змінити роль користувача окремим маршрутом лише SuperAdmin


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
    response_model=UserAdminCreatedUserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully created a new user.",
)
async def create_user_by_admin(
    body: UserAdminCreateRequestSchema,
    user: User = Depends(get_current_active_admin_user),
    user_service: UserService = Depends(get_user_service),
) -> UserAdminCreatedUserResponseSchema:
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

    return UserAdminCreatedUserResponseSchema.model_validate(new_user)
