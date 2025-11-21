"""
Pydantic schemas for auth operations.

Includes response models.
"""

from pydantic import BaseModel, Field

from src.utils.constants import MESSAGE_SUCCESS_EMAIL_VERIFIED

from src.api.schemas.mixins import ExampleGenerationMixin
from .fields import TokenField, TokenTypeField


class LoginTokenResponseSchema(BaseModel):
    """Response schema for issued access token."""

    access_token: str = TokenField(
        description="Issued access JWT token",
        example="<ACCESS_TOKEN>",
    )
    refresh_token: str = TokenField(
        description="Issued refresh JWT token",
        example="<REFRESH_TOKEN>",
    )
    token_type: str = TokenTypeField()


class AccessTokenResponseSchema(BaseModel):
    """Response schema for issued access token."""

    access_token: str = TokenField(
        description="Issued access JWT token",
        example="<ACCESS_TOKEN>",
    )
    token_type: str = TokenTypeField()


class EmailVerificationSuccessResponseSchema(ExampleGenerationMixin, BaseModel):
    """Response schema for successful email verification."""

    detail: str = Field(
        description="JWT token",
        json_schema_extra={"example": MESSAGE_SUCCESS_EMAIL_VERIFIED},
    )
