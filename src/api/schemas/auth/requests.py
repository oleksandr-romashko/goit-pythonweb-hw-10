"""
Pydantic schemas for auth operations.

Includes request models.
"""

from pydantic import BaseModel, SecretStr

from .fields import TokenField


class RefreshTokenRequestSchema(BaseModel):
    """Request schema containing refresh token."""

    refresh_token: SecretStr = TokenField(
        description="Valid refresh JWT token",
        example="<REFRESH_TOKEN>",
    )
