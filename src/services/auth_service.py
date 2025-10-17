"""Service layer providing business logic for managing authentication."""

from typing import Dict, Any, Optional

from src.config import app_config
from src.utils.security.jwt_utils import (
    issue_token,
    decode_token,
    ExpiredTokenError,
    InvalidTokenError,
)
from src.utils.logger import logger

from .errors import InvalidAccessTokenError


class AuthService:
    """Handles business logic related to authentication."""

    def __init__(self, *, secret=None, algorithm=None, expiration_time_seconds=None):
        """Initialize the service with auth settings from app config."""
        self.secret: str = secret or app_config.AUTH_JWT_SECRET
        self.alg: str = algorithm or app_config.AUTH_JWT_ALGORITHM
        self.exp: int = (
            expiration_time_seconds or app_config.AUTH_JWT_EXPIRATION_SECONDS
        )

    def create_access_token(self, user_id: int) -> str:
        """Create access token for user authorization"""
        token_data = issue_token(
            secret_key=self.secret,
            algorithm=self.alg,
            expiration_time_seconds=self.exp,
            subject=str(user_id),
            audience="access_token",
        )
        logger.info(
            "Issued access token '%s' for user with id '%d'.",
            token_data.get("jti"),
            user_id,
        )
        return token_data["token"]

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT access token.

        Ensures:
        - Token is valid and not expired
        - Audience includes 'auth' and 'access'
        - Subject ('sub') is a numeric user ID

        Returns:
            Dict[str, Any]: Decoded JWT payload containing user claims.
        Raises:
            InvalidAccessTokenError: If the token is invalid or malformed.
        """

        try:
            payload = decode_token(
                token=token,
                secret_key=self.secret,
                algorithms=[self.alg],
                audience="access_token",
            )
        except (ExpiredTokenError, InvalidTokenError) as exc:
            raise InvalidAccessTokenError(str(exc)) from exc

        subject_claim: Optional[str] = payload.get("sub")
        if subject_claim is None:
            raise InvalidAccessTokenError("Token has no subject ('sub') claim")

        if not subject_claim.isdigit():
            raise InvalidAccessTokenError(
                "Access token subject ('sub') claim, should be an integer"
            )

        return payload


auth_service = AuthService()
"""Singleton instance of AuthService."""
