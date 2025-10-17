"""Custom exception classes for service-level logic."""


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
