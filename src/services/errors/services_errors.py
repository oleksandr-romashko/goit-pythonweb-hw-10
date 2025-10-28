"""Custom exception classes for service-level logic."""

from src.utils.constants import (
    MESSAGE_ERROR_USER_ROLE_IS_INVALID,
    MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS,
)


class BadProvidedDataError(Exception):
    """Raised when provided data are incorrect."""

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(f"User data conflict: {errors}")

    def __str__(self) -> str:
        return f"UserConflictError(errors={self.errors})"


class InvalidUserCredentialsError(Exception):
    """Raised when provided user credentials are incorrect."""

    def __init__(self, message: str):
        super().__init__(f"Invalid user credentials: {message}")


class UserConflictError(Exception):
    """
    Raised when user data conflicts with existing records
    (e.g., username or email already taken).
    """

    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(f"User data conflict: {errors}")

    def __str__(self) -> str:
        return f"UserConflictError(errors={self.errors})"


class InvalidAccessTokenError(Exception):
    """Raised when an access token is invalid or expired."""

    def __init__(self, message: str):
        super().__init__(f"Invalid access token: {message}")


class UserRoleIsInvalidError(Exception):
    """Raised when user role is not a valid user role."""

    def __init__(self, message: str = MESSAGE_ERROR_USER_ROLE_IS_INVALID):
        super().__init__(message)


class UserRolePermissionError(Exception):
    """Raised when operation can't be done with this role."""

    def __init__(self, message: str = MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS):
        super().__init__(message)


class UserViewPermissionError(Exception):
    """Raised when user is not allowed to view existing user data."""

    def __init__(self, message: str = MESSAGE_ERROR_USER_ROLE_INVALID_PERMISSIONS):
        super().__init__(message)
