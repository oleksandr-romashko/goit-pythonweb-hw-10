"""Module exposing service-level custom exceptions."""

from .services_errors import (
    BadProvidedDataError,
    InvalidUserCredentialsError,
    UserInactiveError,
    UserConflictError,
    InvalidTokenError,
    EmailChangeNotAllowedError,
    UserRoleIsInvalidError,
    UserRolePermissionError,
    UserViewPermissionError,
    UserEmailIsAlreadyConfirmedError,
    FileUploadFailedError,
)

__all__ = [
    "BadProvidedDataError",
    "InvalidUserCredentialsError",
    "UserInactiveError",
    "UserConflictError",
    "InvalidTokenError",
    "EmailChangeNotAllowedError",
    "UserRoleIsInvalidError",
    "UserRolePermissionError",
    "UserViewPermissionError",
    "UserEmailIsAlreadyConfirmedError",
    "FileUploadFailedError",
]
