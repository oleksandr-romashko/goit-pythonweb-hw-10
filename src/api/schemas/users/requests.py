"""
Pydantic schemas for users operations.

Includes request models.
"""

from typing import Optional, Literal

from pydantic import BaseModel, EmailStr

from src.db.models.enums.user_roles import UserRole

from src.api.schemas.validators.common import at_least_one_field_required_validator
from src.api.schemas.validators.users import (
    user_password_strength_validator,
    user_role_exists_validator,
)

from src.api.schemas.common.fields import EmailField
from .enums import UserFilterRole
from .fields import (
    AvatarResetField,
    IsActiveField,
    InactiveLastSortField,
    PasswordField,
    RoleField,
    UsernameField,
)


@user_password_strength_validator
class UserRegisterRequestSchema(BaseModel):
    """Schema for registering of a new user."""

    username: str = UsernameField()
    email: EmailStr = EmailField()
    password: str = PasswordField()


@user_role_exists_validator
@user_password_strength_validator
class UserAdminCreateRequestSchema(UserRegisterRequestSchema):
    """Schema for manual user creation by admin or superadmin."""

    # Inherit fields

    role: str = RoleField(
        optional=True,
        default=UserRole.USER.value,
        description="User role (e.g., user, admin). Only SuperAdmin can create Admins.",
    )
    is_active: Optional[bool] = IsActiveField(optional=True, default=True)

    class Config:
        """Additional model config to forbid adding extra fields"""

        extra = "forbid"


class UserLoginRequestSchema(BaseModel):
    """
    Response schema to login user.

    No need to validate password at login.
    """

    username: str = UsernameField()
    password: str = PasswordField()


@user_password_strength_validator
class UserUpdatePasswordRequestSchema(BaseModel):
    """Schema for updating user password."""

    current_password: Optional[str] = PasswordField(
        optional=True,
        description="Current password to validate",
        example="StrongPass1!",
    )
    password: Optional[str] = PasswordField(
        optional=True, description="New password to set", example="NewStrongPass1!"
    )

    class Config:
        """Additional model config to forbid adding extra fields"""

        extra = "forbid"


@at_least_one_field_required_validator
@user_role_exists_validator
class UserUpdateAdminRequestSchema(BaseModel):
    """Schema for updating existing user by admin user."""

    username: Optional[str] = UsernameField(optional=True)
    is_active: Optional[bool] = IsActiveField(optional=True)
    role: Optional[str] = RoleField(optional=True)

    avatar: Optional[Literal[None]] = AvatarResetField()

    class Config:
        """Additional model config to forbid adding extra fields"""

        extra = "forbid"


class UsersFilterRequestSchema(BaseModel):
    """Schema for filtering users."""

    username: Optional[str] = UsernameField(
        optional=True,
        description=(
            "Filter by username match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
    email: Optional[str] = EmailField(
        optional=True,
        description=(
            "Filter by e-mail match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
    role: Optional[UserFilterRole] = RoleField(
        optional=True,
        description=("Filter by one of available roles"),
    )
    is_active: Optional[bool] = IsActiveField(
        optional=True,
        description=("Filter by active status"),
    )

    inactive_last: bool = InactiveLastSortField(default=False)
