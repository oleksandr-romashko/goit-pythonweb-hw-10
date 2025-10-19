"""Validators for Pydantic schemas for users operations."""

from pydantic import field_validator, model_validator
from pydantic_core import PydanticCustomError

from src.db.models.enums.user_roles import UserRole
from src.utils.constants import AUTH_PASSWORD_SPECIAL_CHARS


def user_password_validator(cls):
    """Decorator adding password field validation"""

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:  # pylint:  disable=w0613
        """Validate password"""
        errors = []

        if not any(c.isupper() for c in v):
            errors.append("must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("must contain at least one number")
        if not any(c in AUTH_PASSWORD_SPECIAL_CHARS for c in v):
            errors.append("must contain at least one special character")

        if errors:
            raise ValueError("; ".join(errors))
        return v

    cls.validate_password = validate_password
    return cls


def user_role_validator(cls):
    """Decorator adding non-exposing validation on the user role."""

    class Wrapper(cls):
        @model_validator(mode="before")
        @classmethod
        def _check_user_role(cls, values):  # pylint:  disable=w0613
            """Check user role within known roles"""

            role = values.get("role")
            if role is not None:
                try:
                    # Check role is valid
                    UserRole(role)
                except ValueError as exc:
                    # Do not provide suggestions to the role, just non-exposing message
                    raise PydanticCustomError("invalid_role", "Invalid role.") from exc
            return values

    return Wrapper
