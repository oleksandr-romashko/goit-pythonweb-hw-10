"""Pydantic field wrappers for users operations."""

from typing import Optional, Any

from pydantic import Field


def UsernameField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
) -> Any:
    """Construct username field with optional validation and value example"""
    return Field(
        None if optional else ...,
        description=description or "User username",
        min_length=3 if validate else None,
        max_length=50 if validate else None,
        json_schema_extra={"example": "JohnDoe"},
    )


def PasswordField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
    example: Optional[str] = None,
) -> Any:
    """Construct password field with optional validation and value example"""
    return Field(
        None if optional else ...,
        description=description or "Strong password",
        min_length=8 if validate else None,
        max_length=128 if validate else None,
        json_schema_extra={"example": example or "StrongPass1!"},
    )


def AvatarField(optional: bool = False) -> Any:  # pylint: disable=invalid-name
    """Construct avatar field with value example"""

    return Field(
        None if optional else ...,
        description="User avatar",
        json_schema_extra={
            "example": "https://www.example.com/avatar/a4b7bd692789b6ba3543cd5194162450"
        },
    )


def AvatarResetField() -> Any:  # pylint: disable=invalid-name
    """Construct avatar field to reset avatar with value example"""
    return Field(
        default=None,
        description=(
            "Optional field to reset user avatar to default (Gravatar). Only null is allowed."
        ),
        json_schema_extra={"example": None},
    )


def IsEmailConfirmedField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:  # pylint: disable=invalid-name
    """Construct email confirmation status field with value example"""

    return Field(
        None if optional else ...,
        description="Email confirmation status",
        json_schema_extra={"example": True},
    )


def RoleField(  # pylint: disable=invalid-name
    optional: bool = False,
    default: Optional[str] = None,
    description: Optional[str] = None,
) -> Any:
    """
    Construct user role field with value example.

    Doesn't validate against UserRoles to avoid exposing full list of roles.
    Validation should occur at the service layer.

    ⚠️ Note:
    - If `optional=True`, the field may be omitted or set to `None`.
    - If `default` is provided, it will be shown as an example in docs even if optional.
    """

    default_value = None if optional else (default if default is not None else ...)
    return Field(
        default_value,
        description=description or "User role (e.g., user, admin, etc.)",
        json_schema_extra={"example": default or "user"},
    )


def IsActiveField(  # pylint: disable=invalid-name
    optional: bool = False,
    default: Optional[bool] = True,
    description: Optional[str] = None,
) -> Any:
    """Construct user active status field with value example"""

    return Field(
        None if optional else default,
        description=description or "User active status",
        json_schema_extra={"example": default or True},
    )


def ContactsField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:
    """Construct contacts field with value example"""

    return Field(
        None if optional else [],
        description="List of user contacts",
        json_schema_extra={"example": "[]"},
    )


def ContactsCountField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:
    """Construct count of user contacts field with default value and value example"""

    return Field(
        None if optional else 0,
        description="Number of associated contacts",
        json_schema_extra={"example": 42},
    )


def InactiveLastSortField(  # pylint: disable=invalid-name
    optional: bool = False,
    default: Optional[bool] = False,
    description: Optional[str] = None,
) -> Any:
    """Construct flag field to show inactive users last with value example"""

    return Field(
        None if optional else default,
        description=description
        or "Show inactive users last. If omitted, defaults to false.",
        json_schema_extra={"example": default or False},
    )
