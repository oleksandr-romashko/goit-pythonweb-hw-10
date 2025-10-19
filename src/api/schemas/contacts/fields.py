"""Pydantic field wrappers for contacts operations."""

from typing import Optional, Any
from datetime import date

from pydantic import Field


def FirstNameField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
) -> Any:
    """Construct first name field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(max_length=50))

    return Field(
        None if optional else ...,
        description=description or "First name",
        **constraints,
        json_schema_extra={"example": "John"},
    )


def LastNameField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
) -> Any:
    """Construct last name field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(max_length=50))

    return Field(
        None if optional else ...,
        description=description or "Last name",
        **constraints,
        json_schema_extra={"example": "Doe"},
    )


def EmailField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
) -> Any:
    """Construct email field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(max_length=150))

    return Field(
        None if optional else ...,
        description=description or "Email address",
        **constraints,
        json_schema_extra={"example": "john.doe@example.com"},
    )


def PhoneNumberField(  # pylint: disable=invalid-name
    optional: bool = False, validate: bool = True
) -> Any:
    """Construct phone number field with optional validation and value example"""
    constraints = {}
    if validate:
        constraints.update(dict(max_length=40))

    return Field(
        None if optional else ...,
        description="Phone number",
        **constraints,
        json_schema_extra={"example": "+123123456789"},
    )


def BirthdateField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:
    """Construct birthdate field with value example"""
    return Field(
        None if optional else ...,
        description="Birthday date",
        json_schema_extra={"example": date(2000, 1, 4).isoformat()},
    )


def InfoField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:
    """Construct informational field for free-form notes with value example"""
    return Field(
        None if optional else ...,
        description="Additional descriptive notes",
        json_schema_extra={
            "example": (
                "Works in automotive. Met at conference in Prague 13.08.2025.\n"
                "Loves cats, allergic to nuts and cocoa."
            )
        },
    )


def CelebrationDateField(  # pylint: disable=invalid-name
    optional: bool = False,
) -> Any:
    """Construct celebration date field with value example"""
    return Field(
        None if optional else ...,
        description="Actual celebration date moved to closest workday",
        json_schema_extra={"example": date(2025, 1, 6).isoformat()},
    )
