"""Pydantic schemas for auth operations."""

from typing import Optional, Any

from pydantic import BaseModel, Field, SecretStr


def TokenField(  # pylint: disable=invalid-name
    optional: bool = False,
    description: Optional[str] = None,
    example: Optional[str] = None,
) -> Any:
    """Construct token field with value example"""

    return Field(
        None if optional else ...,
        description=description or "JWT token",
        json_schema_extra={"example": example or "<TOKEN>"},
    )


def TokenTypeField(  # pylint: disable=invalid-name
    optional: bool = False,
    description: Optional[str] = None,
    example: Optional[str] = None,
) -> Any:
    """Construct token type field with value example"""

    return Field(
        None if optional else ...,
        description=description or "Token type",
        json_schema_extra={"example": example or "bearer"},
    )


class RefreshTokenRequestSchema(BaseModel):
    """Request schema containing refresh token."""

    refresh_token: SecretStr = TokenField(
        description="Valid refresh JWT token",
        example="<REFRESH_TOKEN>",
    )


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
