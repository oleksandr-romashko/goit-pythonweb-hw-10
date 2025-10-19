"""Pydantic field wrappers for users operations."""

from typing import Any

from pydantic import (
    Field,
)


def UsernameField(  # pylint: disable=invalid-name
    optional: bool = False, validate: bool = True
) -> Any:
    """Construct username field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(min_length=3, max_length=50))

    return Field(
        None if optional else ...,
        description="User username",
        **constraints,
        json_schema_extra={"example": "JohnDoe"},
    )


def EmailField(  # pylint: disable=invalid-name
    optional: bool = False, validate: bool = True
) -> Any:
    """Construct email field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(max_length=150))

    return Field(
        None if optional else ...,
        description="Email address",
        **constraints,
        json_schema_extra={"example": "john.doe@example.com"},
    )


def PasswordField(  # pylint: disable=invalid-name
    optional: bool = False, validate: bool = True
) -> Any:
    """Construct password field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(min_length=8, max_length=128))

    return Field(
        None if optional else ...,
        description="Strong password",
        **constraints,
        json_schema_extra={"example": "StrongPass1!"},
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


def RoleField(optional: bool = False) -> Any:  # pylint: disable=invalid-name
    """Construct user role field with value example"""

    return Field(
        None if optional else ...,
        description="User role (e.g., user, admin, etc.)",
        json_schema_extra={"example": "admin"},
    )


def IsActiveField(optional: bool = False) -> Any:  # pylint: disable=invalid-name
    """Construct user active status field with value example"""

    return Field(
        None if optional else ...,
        description="User active status",
        json_schema_extra={"example": True},
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
