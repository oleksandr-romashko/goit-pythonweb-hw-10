"""
Pydantic schemas for auth operations.

Includes request models.
"""

from pydantic import BaseModel, EmailStr, SecretStr

from src.api.schemas.common.fields import EmailField
from .fields import TokenField


class EmailRequestSchema(BaseModel):
    """Request schema containing email address."""

    email: EmailStr = EmailField()


class RefreshTokenRequestSchema(BaseModel):
    """Request schema containing refresh token."""

    refresh_token: SecretStr = TokenField(
        description="Valid refresh JWT token",
        example="<REFRESH_TOKEN>",
    )
