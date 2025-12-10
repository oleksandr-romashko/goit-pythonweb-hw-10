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


class EmailTokenType(str, Enum):
    """Enum representing email token types."""

    CONFIRMATION = "email_confirmation_token"


class TokenAudience(str, Enum):
    """Enum representing token audience (aud claim)"""

    API = "api"
    EMAIL = "email"


class AuthService:
    """Handles business logic related to authentication."""

    def __init__(
        self,
        *,
        access_secret: Optional[str] = None,
        email_secret: Optional[str] = None,
        algorithm: Optional[str] = None,
        access_expiration: Optional[int] = None,
        refresh_expiration: Optional[int] = None,
        email_confirmation_expiration: Optional[int] = None,
    ):
        """Initialize the service with auth settings from app config."""
        self.access_secret = access_secret or app_config.AUTH_JWT_SECRET
        self.email_secret = email_secret or app_config.MAIL_JWT_SECRET
        self.alg = algorithm or app_config.AUTH_JWT_ALGORITHM
        self.access_token_exp = (
            access_expiration or app_config.AUTH_JWT_ACCESS_EXPIRATION_SECONDS
        )
        self.refresh_exp = (
            refresh_expiration or app_config.AUTH_JWT_REFRESH_EXPIRATION_SECONDS
        )
        self.email_confirmation_token_exp = (
            email_confirmation_expiration
            or app_config.MAIL_JWT_CONFIRMATION_EXPIRATION_SECONDS
        )

    def create_access_token(self, user_id: int) -> str:
        """Create a signed JWT access token for a given user ID."""
        return self._create_auth_token(user_id, AuthTokenType.ACCESS)

    def create_refresh_token(self, user_id: int) -> str:
        """Create a signed JWT refresh token for a given user ID."""
        return self._create_auth_token(user_id, AuthTokenType.REFRESH)

    def create_email_confirmation_token(self, user_id: int, email: str) -> str:
        """Create a signed JWT email confirmation token for a given user ID and email."""
        return self._create_email_token(user_id, email, EmailTokenType.CONFIRMATION)

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

    def decode_email_verification_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT email confirmation token.

        Example decoded token payload:
        {
            'token_type': 'email_confirmation_token',  # type of the token
            'aud': 'email',                            # audience claim
            'sub': '1',                                # user ID as a string
            'email': 'user@example.com',               # email associated with the token
            'jti': '33113437-53a9-46b3-b8e2-...',      # unique token identifier
            'iat': 1763667153,                         # issued at timestamp
            'exp': 1763753553                          # expiration timestamp
        }
        """
        return self._decode_email_token(
            token, EmailTokenType.CONFIRMATION, enforce_numeric_sub=True
        )

    def _create_auth_token(self, user_id: int, token_type: AuthTokenType) -> str:
        """
        Create a signed JWT authentication token of a given token type.

        Args:
            user_id (int): User ID as a payload to encode into the JWT.
            token_type (AuthTokenType): Type of the authentication token.

        Returns:
            str: Encoded JWT token (Base64 string) ready for use in Authorization header.

        Raises:
            ValueError: If unsupported token type is provided.
            InvalidAccessTokenError: If the token is invalid or malformed.
        """

        if token_type not in AuthTokenType:
            raise ValueError(f"Unsupported auth token type: {token_type}")

        expiration = 0
        if token_type == AuthTokenType.ACCESS:
            expiration = self.access_token_exp
        elif token_type == AuthTokenType.REFRESH:
            expiration = self.refresh_exp
        else:
            raise ValueError(f"Unsupported auth token type: {token_type}")

        token_data = issue_token(
            secret_key=self.access_secret,
            algorithm=self.alg,
            expiration_time_seconds=expiration,
            subject=str(user_id),
            audience=TokenAudience.API.value,
            data={"token_type": token_type.value},
        )

        logger.info(
            "Issued %s for user with user_id=%s (jti=%s).",
            token_type.value,
            user_id,
            token_data.get("jti"),
        )

        return token_data["token"]

    def _create_email_token(
        self, user_id: int, email: str, token_type: EmailTokenType
    ) -> str:
        """
        Create a signed JWT email token of a given token type.

        Args:
            user_id (int): User ID as a payload to encode into the JWT.
            email (str): Email address associated with the token.
            token_type (EmailTokenType): Type of the email token.

        Returns:
            str: Encoded JWT token (Base64 string) ready for use in emails links.
        """

        if token_type not in EmailTokenType:
            raise ValueError(f"Unsupported email token type: {token_type}")

        expiration = 0
        if token_type == EmailTokenType.CONFIRMATION:
            expiration = self.email_confirmation_token_exp
        else:
            raise ValueError(f"Unsupported email token type: {token_type}")

        token_data = issue_token(
            secret_key=self.email_secret,
            algorithm=self.alg,
            expiration_time_seconds=expiration,
            subject=str(user_id),
            audience=TokenAudience.EMAIL.value,
            data={
                "token_type": token_type.value,
                "email": email,
            },
        )

        logger.info(
            "Issued %s for user with user_id=%s (jti=%s).",
            token_type.value,
            user_id,
            token_data.get("jti"),
        )

        return token_data["token"]

    def _decode_auth_token(
        self, token: str, token_type: AuthTokenType, *, enforce_numeric_sub: bool = True
    ) -> Dict[str, Any]:
        """
        Decode and validate JWT authentication token.

        Ensures:
        - Token is valid and not expired
        - Audience includes 'api' value
        - Subject ('sub') is a numeric user ID with check if enforce_numeric_sub = True

        Args:
            token (str): The encoded JWT token string.
            token_type (TokenType): Type of token.
            enforce_numeric_sub (bool): Whether to enforce that 'sub' claim is numeric.

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
                expected_audience=TokenAudience.API.value,
                expected_token_type=token_type.value,
            )
        except MalformedTokenError as exc:
            logger.debug("Token is malformed and invalid: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc
        except ExpiredTokenError as exc:
            logger.debug("Token has no subject ('sub') claim: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc

        subject_claim: Optional[str] = payload.get("sub")
        if not subject_claim:
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
            "Decoded and validated %s for user with user_id=%s (jti=%s).",
            token_type.value,
            payload.get("sub", "unknown"),
            payload.get("jti", "unknown"),
        )

        return payload

    def _decode_email_token(
        self,
        token: str,
        token_type: EmailTokenType,
        *,
        enforce_numeric_sub: bool = True,
    ) -> Dict[str, Any]:
        """
        Decode and validate JWT email token.

        Ensures:
        - Token is valid and not expired
        - Audience includes 'email' value
        - Subject ('sub') is a numeric user ID with check if enforce_numeric_sub = True

        Args:
            token (str): The encoded JWT token string.
            token_type (TokenType): Type of token.
            enforce_numeric_sub (bool): Whether to enforce that 'sub' claim is numeric.

        Returns:
            Dict[str, Any]: Decoded JWT payload containing user claims.

        Raises:
            ValueError: If unsupported token type is provided.
            InvalidAccessTokenError: If the token is invalid or malformed.
        """
        if token_type not in EmailTokenType:
            raise ValueError(f"Unsupported email token type: {token_type}")

        payload = {}
        try:
            payload = decode_token(
                token=token,
                secret_key=self.email_secret,
                algorithms=[self.alg],
                expected_audience=TokenAudience.EMAIL.value,
                expected_token_type=token_type.value,
            )
        except MalformedTokenError as exc:
            logger.debug("Token is malformed and invalid: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc
        except ExpiredTokenError as exc:
            logger.debug("Token has no subject ('sub') claim: %s", str(exc))
            raise InvalidTokenError(str(exc)) from exc

        subject_claim: Optional[str] = payload.get("sub")
        if not subject_claim:
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

        email_claim: Optional[str] = payload.get("email")
        if not email_claim:
            logger.debug(
                "Token jti=%s has no email ('email') claim",
                payload.get("jti", "unknown"),
            )
            raise InvalidTokenError("Token has no email ('email') claim")

        logger.debug(
            "Decoded and validated %s for user with user_id=%s (jti=%s).",
            token_type.value,
            payload.get("sub", "unknown"),
            payload.get("jti", "unknown"),
        )

        return payload


auth_service = AuthService()
"""Default AuthService instance."""
