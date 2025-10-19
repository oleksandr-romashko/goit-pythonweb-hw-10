"""Pydantic schemas for users operations."""

from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
)

from src.api.schemas.validators.common import at_least_one_field_required_validator
from src.api.schemas.validators.users import (
    user_password_strength_validator,
    user_role_exists_validator,
)

from .fields import (
    UsernameField,
    EmailField,
    PasswordField,
    AvatarField,
    RoleField,
    IsActiveField,
)


@user_password_strength_validator
class UserRegisterRequestSchema(BaseModel):
    """Schema for registering of a new user."""

    username: str = UsernameField()
    email: EmailStr = EmailField()
    password: str = PasswordField()


class UserLoginRequestSchema(BaseModel):
    """
    Response schema to login user.

    No need to validate password at login.
    """

    username: str = UsernameField()
    password: str = PasswordField()


@at_least_one_field_required_validator
@user_password_strength_validator
class UserUpdateRequestSchema(BaseModel):
    """Schema for updating existing user by regular user."""

    email: Optional[EmailStr] = EmailField(optional=True)
    password: Optional[str] = PasswordField(optional=True)
    avatar: Optional[str] = AvatarField(optional=True)


@user_role_exists_validator
class UserUpdateAdminRequestSchema(UserUpdateRequestSchema):
    """Schema for updating existing user by admin user."""

    username: Optional[str] = UsernameField(optional=True)
    role: Optional[str] = RoleField(optional=True)
    is_active: Optional[bool] = IsActiveField(optional=True)
