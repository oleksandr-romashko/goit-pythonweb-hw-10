"""Module exposing service-level custom exceptions."""

from .services_errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    UserConflictError,
    InvalidAccessTokenError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
    UserViewPermissionError,
)

__all__ = [
    "BadProvidedDataError",
    "InvalidUserCredentialsError",
    "UserConflictError",
    "InvalidAccessTokenError",
    "UserRoleIsInvalidError",
    "UserRolePermissionError",
    "UserViewPermissionError",
]
