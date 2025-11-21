"""Pydantic field wrappers for auth operations."""

from typing import Optional, Any

from pydantic import Field


def TokenField(  # pylint: disable=invalid-name
    optional: bool = False,
    description: Optional[str] = None,
    example: Optional[str] = None,
) -> Any:
    """Construct token field with value example"""

    return Field(
        None if optional else ...,
        description=description or "JWT token",
        json_schema_extra={"example": example or "<TOKEN>"},
    )


def TokenTypeField(  # pylint: disable=invalid-name
    optional: bool = False,
    description: Optional[str] = None,
    example: Optional[str] = None,
) -> Any:
    """Construct token type field with value example"""

    return Field(
        None if optional else ...,
        description=description or "Token type",
        json_schema_extra={"example": example or "bearer"},
    )
