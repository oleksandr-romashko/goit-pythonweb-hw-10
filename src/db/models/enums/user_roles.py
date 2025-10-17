"""User role enumeration."""

from enum import StrEnum


class UserRole(StrEnum):
    """Defines available roles for application users."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
