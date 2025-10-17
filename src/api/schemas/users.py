"""Pydantic schemas for users operations."""

from typing import List, Optional, Union, Annotated

from pydantic import RootModel, BaseModel, EmailStr, Field, field_validator

from src.utils.constants import AUTH_PASSWORD_SPECIAL_CHARS

from .contacts import ContactModelSchema
from .mixins import (
    FromOrmAttributesConfig,
    IdMixin,
    TimestampsMixin,
    UserRoleMixin,
    ContactsCountMixin,
    ExampleMixin,
)


class UserModelSchema(IdMixin, TimestampsMixin, FromOrmAttributesConfig, BaseModel):
    """Schema for user model, excluding sensitive data."""

    username: str = Field(
        description="User username",
        min_length=3,
        max_length=50,
        json_schema_extra={"example": "JohnDoe"},
    )
    email: EmailStr = Field(
        description="E-mail address",
        max_length=150,
        json_schema_extra={"example": "john.doe@example.com"},
    )
    avatar: Optional[str] = Field(
        None,
        json_schema_extra={
            "example": "https://www.gravatar.com/avatar/a4b7bd692789b6ba3543cd5194162450"
        },
    )

    contacts: Optional[List[ContactModelSchema]] = Field(
        None,
        description="List of user contacts",
        json_schema_extra={"example": "[]"},
    )


class UserRegisterRequestSchema(BaseModel):
    """Schema for registering of a new user."""

    username: str = Field(
        description="User username",
        min_length=3,
        max_length=50,
        json_schema_extra={"example": "JohnDoe"},
    )
    email: EmailStr = Field(
        description="E-mail address",
        max_length=150,
        json_schema_extra={"example": "john.doe@example.com"},
    )
    password: str = Field(
        description="Strong password",
        min_length=8,
        max_length=128,
        json_schema_extra={"example": "StrongPass1!"},
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password field for better security"""
        errors = []

        if not any(c.isupper() for c in v):
            errors.append("must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("must contain at least one number")
        if not any(c in AUTH_PASSWORD_SPECIAL_CHARS for c in v):
            errors.append("must contain at least one special character")

        if errors:
            # Create single user-friendly message from all errors
            error_message = "; ".join(errors)
            raise ValueError(f"Password {error_message}.")

        return v


class UserLoginRequestSchema(BaseModel):
    """Response schema to login user."""

    username: str = Field(
        description="User username",
        json_schema_extra={"example": "JohnDoe"},
    )
    password: str = Field(
        description="Strong password",
        json_schema_extra={"example": "StrongPass1!"},
    )


class UserResponseSchema(ExampleMixin, FromOrmAttributesConfig, BaseModel):
    """Response schema to represent user data."""

    username: str = Field(
        json_schema_extra={"example": "JohnDoe"},
    )
    email: EmailStr = Field(
        json_schema_extra={"example": "john.doe@example.com"},
    )
    avatar: Optional[str] = Field(
        None,
        json_schema_extra={
            "example": "https://www.gravatar.com/avatar/a4b7bd692789b6ba3543cd5194162450"
        },
    )


class UserRegisteredResponseSchema(ContactsCountMixin, UserResponseSchema):
    """Response schema to represent newly created user data."""


class UserAboutMeResponseSchema(ContactsCountMixin, UserResponseSchema):
    """Response schema to represent information about the current user."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "JohnDoe",
                    "email": "john.doe@example.com",
                    "avatar": "https://example.com/avatar.png",
                    "contacts_count": 5,
                }
            ]
        }
    }


class UserAboutMeAdminResponseSchema(
    TimestampsMixin, UserRoleMixin, UserAboutMeResponseSchema
):
    """Response schema to represent information about the current user viewed by admin users."""


class UserAboutMeOneOfResponseSchema(RootModel):
    """Response schema to represent one of schemas for information about the current user."""

    root: Annotated[
        Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema], "oneOf"
    ]
