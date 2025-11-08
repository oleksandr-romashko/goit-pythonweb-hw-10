"""Application user roles."""

from enum import StrEnum


class UserRole(StrEnum):
    """
    Defines available roles for application users.

    Roles:
        SUPERADMIN - Full control over the system.
            • Manages app settings and services.
            • Performs system monitoring.
            • Manages other users (ADMIN, MODERATOR, USER).

        ADMIN - Manages registered users (MODERATOR, USER).

        MODERATOR - Manages site content (news, media, menu, events, special offers, etc.).

        USER - Regular registered user. Can view content, place orders, comment, manage profile.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
