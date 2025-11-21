"""Pydantic field wrappers common for various operations."""

from typing import Optional, Any

from pydantic import Field


def EmailField(  # pylint: disable=invalid-name
    optional: bool = False,
    validate: bool = True,
    description: Optional[str] = None,
) -> Any:
    """Construct email field with optional validation and value example"""
    return Field(
        None if optional else ...,
        description=description or "Email address",
        max_length=150 if validate else None,
        json_schema_extra={"example": "john.doe@example.com"},
    )
