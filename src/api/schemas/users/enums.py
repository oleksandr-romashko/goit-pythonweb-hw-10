"""Enums for users Pydantic field wrappers."""

from enum import StrEnum

from src.db.models.enums.user_roles import UserRole


class UserFilterRole(StrEnum):
    """Defines available filter values for user roles."""

    USER = UserRole.USER
    MODERATOR = UserRole.MODERATOR
    ADMIN = UserRole.ADMIN
