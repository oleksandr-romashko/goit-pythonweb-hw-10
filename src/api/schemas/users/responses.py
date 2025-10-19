"""Pydantic schemas for users operations."""

from typing import Optional, Union, Annotated

from pydantic import (
    RootModel,
    BaseModel,
    EmailStr,
)

from src.api.schemas.mixins import (
    FromOrmAttributesConfig,
    TimestampsMixin,
    ExampleGenerationMixin,
)

from .fields import (
    UsernameField,
    EmailField,
    AvatarField,
    RoleField,
    ContactsCountField,
)


class UserResponseSchema(ExampleGenerationMixin, FromOrmAttributesConfig, BaseModel):
    """Response schema to represent user data."""

    username: str = UsernameField(validate=False)
    email: EmailStr = EmailField(validate=False)
    avatar: Optional[str] = AvatarField(optional=True)


class UserRegisteredResponseSchema(UserResponseSchema):
    """Response schema to represent newly created user data."""

    contacts_count: int = ContactsCountField()


class UserAboutMeResponseSchema(UserResponseSchema):
    """Response schema to represent information about the current user."""

    contacts_count: int = ContactsCountField()


class UserAboutMeAdminResponseSchema(TimestampsMixin, UserAboutMeResponseSchema):
    """Response schema to represent information about the current user viewed by admin users."""

    role: Optional[str] = RoleField(optional=True)


class UserAboutMeOneOfResponseSchema(RootModel):
    """Response schema to represent one of schemas for information about the current user."""

    root: Annotated[
        Union[UserAboutMeResponseSchema, UserAboutMeAdminResponseSchema], "oneOf"
    ]
