"""
Common helpers for raising FastAPI HTTP exceptions with consistent payloads.
"""

from typing import NoReturn

from fastapi import HTTPException, status


def raise_http_404_error(message: str = "Not found") -> NoReturn:
    """Raise a 404 Not Found error with a consistent payload."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def raise_http_409_error(message: str = "Resource already exists") -> NoReturn:
    """Raise a 409 Conflict error with a consistent payload."""
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def raise_http_500_error(message: str = "Internal Server Error") -> NoReturn:
    """Raise a 500 Internal Server Error with a consistent payload."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message,
    )
