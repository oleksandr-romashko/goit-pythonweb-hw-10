"""
Common helpers for raising FastAPI HTTP exceptions with consistent payloads.
"""

from typing import NoReturn, Optional, Dict

from fastapi import HTTPException, status

from src.utils.constants import (
    MESSAGE_ERROR_UNAUTHORIZED,
    MESSAGE_ERROR_FORBIDDEN,
    MESSAGE_ERROR_NOT_FOUND,
    MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS,
    MESSAGE_ERROR_INTERNAL_SERVER_ERROR,
)


def raise_http_401_error(message: str = MESSAGE_ERROR_UNAUTHORIZED) -> NoReturn:
    """Raise a 401 Unauthorized error with a consistent payload."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": 'Bearer realm="api/auth/login"'},
    )


def raise_http_403_error(message: str = MESSAGE_ERROR_FORBIDDEN) -> NoReturn:
    """Raise a 403 Forbidden error with a consistent payload."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
        headers={"WWW-Authenticate": 'Bearer realm="api/auth/login"'},
    )


def raise_http_404_error(message: str = MESSAGE_ERROR_NOT_FOUND) -> NoReturn:
    """Raise a 404 Not Found error with a consistent payload."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def raise_http_409_error(
    message: str = MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS, detail: Optional[Dict] = None
) -> NoReturn:
    """Raise a 409 Conflict error with a consistent payload."""
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail or message)


def raise_http_500_error(
    message: str = MESSAGE_ERROR_INTERNAL_SERVER_ERROR,
) -> NoReturn:
    """Raise a 500 Internal Server Error with a consistent payload."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    )
