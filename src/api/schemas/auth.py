"""Pydantic schemas for auth operations."""

from pydantic import BaseModel


class AccessTokenResponseSchema(BaseModel):
    """Response schema for issued access token."""

    access_token: str
    token_type: str
