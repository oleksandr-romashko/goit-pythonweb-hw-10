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


class AuthTokenType(str, Enum):
    """Enum representing authentication token types."""

    ACCESS = "access_token"
    REFRESH = "refresh_token"


class TokenAudience(str, Enum):
    """Enum representing token audience (aud claim)"""

    API = "api"


class AuthService:
    """Handles business logic related to authentication."""

    def __init__(
        self,
        *,
        access_secret: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_expiration: Optional[int] = None,
        refresh_expiration: Optional[int] = None,
    ):
        """Initialize the service with auth settings from app config."""
        self.access_secret = access_secret or app_config.AUTH_JWT_SECRET
        self.alg = algorithm or app_config.AUTH_JWT_ALGORITHM
        self.access_token_exp = (
            access_expiration or app_config.AUTH_JWT_ACCESS_EXPIRATION_SECONDS
        )
        self.refresh_exp = (
            refresh_expiration or app_config.AUTH_JWT_REFRESH_EXPIRATION_SECONDS
        )

    def create_access_token(self, user_id: int) -> str:
        """Create a signed JWT access token for a given user ID."""
        return self._create_auth_token(user_id, AuthTokenType.ACCESS)

    def create_refresh_token(self, user_id: int) -> str:
        """Create a signed JWT refresh token for a given user ID."""
        return self._create_auth_token(user_id, AuthTokenType.REFRESH)

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT access token."""
        return self._decode_auth_token(
            token, AuthTokenType.ACCESS, enforce_numeric_sub=True
        )

    def decode_refresh_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT refresh token."""
        return self._decode_auth_token(
            token, AuthTokenType.REFRESH, enforce_numeric_sub=True
        )

    def _create_auth_token(self, user_id: int, token_type: AuthTokenType) -> str:
        """
        Create a signed JWT authentication token of a given type (access or refresh).

        Args:
            user_id (int): User ID as a payload to encode into the JWT.
            token_type (TokenType): Type of the token.

        Returns:
            str: Encoded JWT token (Base64 string) ready for use in Authorization header.
        """

        if token_type not in AuthTokenType:
            raise ValueError(f"Unsupported auth token type: {token_type}")

        expiration = 0
        if token_type == AuthTokenType.ACCESS:
            expiration = self.access_token_exp
        elif token_type == AuthTokenType.REFRESH:
            expiration = self.refresh_exp

        token_data = issue_token(
            secret_key=self.access_secret,
            algorithm=self.alg,
            expiration_time_seconds=expiration,
            subject=str(user_id),
            audience=TokenAudience.API.value,
            data={"token_type": token_type.value},
        )

        logger.info(
            "Issued %s for user with user_id=%d (jti=%s).",
            token_type.value,
            token_data.get("jti"),
            user_id,
        )

        return token_data["token"]

    def _decode_auth_token(
        self, token: str, token_type: AuthTokenType, *, enforce_numeric_sub: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate JWT authentication token.

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
        if token_type not in AuthTokenType:
            raise ValueError(f"Unsupported auth token type: {token_type}")

        payload = {}
        try:
            payload = decode_token(
                token=token,
                secret_key=self.access_secret,
                algorithms=[self.alg],
                audience=TokenAudience.API.value,
                token_type=token_type.value,
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

        logger.debug(
            "Decoded and validated %s for user with user_id=%d (jti=%s).",
            token_type.value,
            payload.get("sub", "unknown"),
            payload.get("jti", "unknown"),
        )

        return payload


auth_service = AuthService()
"""Singleton instance of AuthService."""
