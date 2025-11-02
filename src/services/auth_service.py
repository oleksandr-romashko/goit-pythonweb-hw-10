"""Service layer providing business logic for managing authentication."""

from enum import Enum
from typing import Dict, Any, Optional

from src.config import app_config
from src.utils.security.jwt_utils import (
    issue_token,
    decode_token,
    ExpiredTokenError,
    MalformedTokenError,
)
from src.utils.logger import logger

from .errors import InvalidTokenError


class TokenType(str, Enum):
    """Enum representing token type"""

    ACCESS = "access_token"
    REFRESH = "refresh_token"


class AuthService:
    """Handles business logic related to authentication."""

    def __init__(
        self,
        *,
        secret=None,
        algorithm=None,
        access_expiration=None,
        refresh_expiration=None,
    ):
        """Initialize the service with auth settings from app config."""
        self.secret: str = secret or app_config.AUTH_JWT_SECRET
        self.alg: str = algorithm or app_config.AUTH_JWT_ALGORITHM
        self.access_exp = (
            access_expiration or app_config.AUTH_JWT_ACCESS_EXPIRATION_SECONDS
        )
        self.refresh_exp = (
            refresh_expiration or app_config.AUTH_JWT_REFRESH_EXPIRATION_SECONDS
        )

    def create_token(self, user_id: int, token_type: TokenType) -> str:
        """
        Create a signed JWT token of a given type (access or refresh).

        Args:
            user_id (int): User ID as a payload to encode into the JWT.
            token_type (TokenType): Type of the token.

        Returns:
            str: Encoded JWT token (Base64 string) ready for use in Authorization header.
        """

        expiration = (
            self.refresh_exp if token_type == TokenType.REFRESH else self.access_exp
        )

        token_data = issue_token(
            secret_key=self.secret,
            algorithm=self.alg,
            expiration_time_seconds=expiration,
            subject=str(user_id),
            audience=token_type.value,
        )
        logger.info(
            "Issued %s (jwt_id=%s) for user with user_id=%d.",
            token_type.value,
            token_data.get("jti"),
            user_id,
        )
        return token_data["token"]

    def decode_token(
        self, token: str, token_type: TokenType, *, enforce_numeric_sub: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate JWT token.

        Ensures:
        - Token is valid and not expired
        - Audience includes 'access_token' or 'refresh_token' value (depending on token type)
        - Subject ('sub') is a numeric user ID with check if enforce_numeric_sub = True

        Args:
            token (str): The encoded JWT token string.
            token_type (TokenType): Type of token.

        Returns:
            Dict[str, Any]: Decoded JWT payload containing user claims.

        Raises:
            InvalidAccessTokenError: If the token is invalid or malformed.
        """
        payload = {}
        try:
            payload = decode_token(
                token=token,
                secret_key=self.secret,
                algorithms=[self.alg],
                audience=token_type.value,
            )
        except MalformedTokenError as exc:
            logger.debug("Token is malformed and invalid: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc
        except ExpiredTokenError as exc:
            logger.debug("Token has no subject ('sub') claim: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc

        subject_claim: Optional[str] = payload.get("sub")
        if subject_claim is None:
            logger.debug(
                "Token jti=%s has no subject ('sub') claim",
                payload.get("jti", "unknown"),
            )
            raise InvalidTokenError("Token has no subject ('sub') claim")

        if enforce_numeric_sub and not subject_claim.isdigit():
            logger.debug(
                "Token jti=%s subject ('sub') claim must be numeric",
                payload.get("jti", "unknown"),
            )
            raise InvalidTokenError(
                f"Token ({token_type.value}) subject ('sub') claim must be numeric"
            )

        return payload


auth_service = AuthService()
"""Singleton instance of AuthService."""
