"""
JWT utilities for creating and decoding JSON Web Tokens (JWTs) with standard and custom claims.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt, JWTError  # type: ignore[import]
from jose.exceptions import ExpiredSignatureError  # type: ignore[import]

from src.utils.logger import logger


class TokenError(Exception):
    """Base class for all token-related errors."""


class MalformedTokenError(TokenError):
    """Raised when the token is malformed or signature validation fails."""


class ExpiredTokenError(TokenError):
    """Raised when the token has expired."""


def issue_token(
    *,
    secret_key: str,
    algorithm: str,
    expiration_time_seconds: int,
    subject: Optional[str] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
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
    if audience:  # not None or empty list
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

    logger.debug(
        "Created JWT token for user_id=%s (token identifier claim jti=%s)",
        payload.get("sub"),
        token_id,
    )

    return {
        "jti": token_id,
        "token": jwt.encode(payload, key=secret_key, algorithm=algorithm),
    }


def decode_token(
    token: str,
    secret_key: str,
    algorithms: List[str],
    audience: Optional[str] = None,
    token_type: Optional[str] = None,
    verify_nbf: bool = True,
    verify_exp: bool = True,
) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    This function performs full JWT validation, including signature verification,
    optional audience checking, expiration and "not before" checks, and an
    optional check of the custom `token_type` claim.

    Args:
        token (str):
            The encoded JWT string.
        secret_key (str):
            Secret key used to verify the token signature.
        algorithms (list[str]):
            A list of allowed signing algorithms (e.g., ["HS256"]).
        audience (str | None):
            Expected `aud` claim. If provided, audience validation is enabled.
            If `None`, the audience check is skipped.
        token_type (str | None):
            Expected custom `token_type` claim value.
            If provided, the decoded token must contain a matching `token_type`.
            If `None`, this validation is skipped.
        verify_nbf (bool):
            Whether to validate the `nbf` ("not before") claim.
        verify_exp (bool):
            Whether to validate the `exp` (expiration) claim.

    Returns:
        dict[str, Any]:
            The decoded JWT payload containing standard and custom claims.

    Raises:
        ExpiredTokenError:
            If the token is expired (`exp`) or not yet valid (`nbf`).
        MalformedTokenError:
            If the token is invalid, the signature is incorrect,
            required claims are missing or malformed,
            or the `token_type` does not match the expected value.

    Notes:
        - Signature verification is always enabled.
        - Audience validation is enabled only if `audience` is provided.
        - Standard JWT claims (`exp`, `nbf`, `iat`) are validated according
          to the provided flags.
    """
    try:
        payload: Dict[str, Any] = jwt.decode(
            token=token,
            key=secret_key,
            algorithms=algorithms,
            audience=audience,
            options={
                "verify_aud": audience is not None,
                "verify_nbf": verify_nbf,
                "verify_exp": verify_exp,
                "verify_signature": True,
            },
        )
        if "jti" not in payload:
            raise MalformedTokenError("Missing 'jti' claim in token payload.")
        if token_type:
            actual_token_type = payload.get("token_type")
            if actual_token_type != token_type:
                raise MalformedTokenError(
                    f"Invalid token type: expected '{token_type}', got '{actual_token_type}'"
                )
        return payload
    except ExpiredSignatureError as exc:
        logger.debug("JWT decode failed: token expired.")
        raise ExpiredTokenError("The token has expired.") from exc
    except JWTError as exc:
        logger.debug("JWT decode failed: invalid token or signature.")
        raise MalformedTokenError("Invalid token or signature.") from exc
