"""
JWT utilities for creating and decoding JSON Web Tokens (JWTs) with standard and custom claims.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError


class TokenError(Exception):
    """Base class for all token-related errors."""


class InvalidTokenError(TokenError):
    """Raised when the token is malformed or signature validation fails."""


class ExpiredTokenError(TokenError):
    """Raised when the token has expired."""


def create_access_token(
    *,
    secret_key: str,
    algorithm: str,
    expiration_time_seconds: int,
    subject: Optional[str] = None,
    issuer: Optional[str] = None,
    audience: Optional[List[str]] = None,
    not_before: Optional[datetime] = None,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Create and sign a JSON Web Token (JWT) with standard and custom claims.

    Args:
        secret_key (str): Secret key used to sign the token.
        algorithm (str): Signing algorithm (e.g., "HS256").
        expiration_time_seconds (int): Token lifetime in seconds.
        subject (str | None): Subject — usually the user ID.
        issuer (str | None): Issuer — identifies the token issuer (e.g., "myapp.com").
        audience (list[str] | None): Audience — who the token is intended for (e.g. "web", "admin").
        not_before (datetime | None): Time before which the token is not valid (`nbf` claim).
        data (dict | None): Additional custom claims to include in the payload.

    Returns:
        dict[str, str]: A dictionary containing:
            - "jti": JWT ID - unique token identifier (for tracking / revocation).
            - "token": Encoded JWT string.

    Notes:
        - Token automatically includes the following standard claims:
            * `jti` (JWT ID) — unique token identifier.
            * `iat` (Issued At) — timestamp when the token was created.
            * `exp` (Expiration Time) — timestamp when the token expires.
            * Optionally includes `sub`, `iss`, `aud`, and `nbf` if provided.
        - Standard claims override any conflicting custom claims from `data`.
        - Follows the JWT RFC 7519 specification.
        - All parameters must be passed explicitly.

    Example:
        result = create_access_token(
            subject="user_123",
            issuer="myapp.local",
            audience=["web", "mobile"],
            data={"role": "admin"},
            secret_key="my_secret",
            algorithm="HS256",
            expiration_time_seconds=3600,
        )
        print(result["token"])  # Encoded JWT
        print(result["jti"])    # Token ID
    """

    # Custom optional claims
    payload: Dict[str, Any] = data.copy() if data else {}

    # Standard optional claims
    if subject is not None:
        payload["sub"] = str(subject)
    if issuer is not None:
        payload["iss"] = issuer
    if audience is not None:
        payload["aud"] = audience
    if not_before is not None:
        payload["nbf"] = int(not_before.timestamp())

    # Technical obligatory claims
    token_id = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=expiration_time_seconds)
    payload.update(
        {
            "jti": token_id,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
    )

    return {
        "jti": token_id,
        "token": jwt.encode(payload, key=secret_key, algorithm=algorithm),
    }


def decode_access_token(
    token: str,
    secret_key: str,
    algorithms: List[str],
    verify_nbf: bool = True,
    verify_exp: bool = True,
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token (str): Encoded JWT string.
        secret_key (str): Secret key used for decoding.
        algorithms (list[str]): Allowed signing algorithm(s).
        verify_nbf (bool): Whether to verify token activation time (`nbf` (not before) claim).
        verify_exp (bool): Whether to verify token expiration (`exp` (expiration) claim).

    Returns:
        dict[str, Any]: Decoded payload with standard and custom claims.

    Raises:
        ExpiredTokenError: If the token has expired (`exp` (expiration) claim)
                           or not active yet (`nbf` (not before) claim).
        InvalidTokenError: If the token signature or structure is invalid.

    Notes:
        - Automatically validates signature and standard claims (`exp` (expiration),
          `nbf` (not before), `iat` (issued at)).
        - Use in services that require trusted token validation before further checks.
    """
    try:
        payload: Dict[str, Any] = jwt.decode(
            token=token,
            key=secret_key,
            algorithms=algorithms,
            options={"verify_nbf": verify_nbf, "verify_exp": verify_exp},
        )
        return payload
    except ExpiredSignatureError as exc:
        raise ExpiredTokenError("The token has expired.") from exc
    except JWTError as exc:
        raise InvalidTokenError("Invalid token or signature.") from exc
