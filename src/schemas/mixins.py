from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseORMModel(BaseModel):
    """
    Base schema with ORM support via `from_attributes`.

    Adds reading the instance attributes corresponding to the model field names.
    Provides integration with object-relational mappings (ORMs).
    """

    model_config = ConfigDict(from_attributes=True)


class IdMixin(BaseModel):
    """Adds an integer `id` field to a schema."""

    id: int = Field(json_schema_extra={"example": 1})


class TimestampsMixin(BaseModel):
    """Adds optional `created_at` and `updated_at` timestamp fields to a schema."""

    created_at: Optional[datetime] = Field(
        None, json_schema_extra={"example": "2025-01-01T12:00:00.392Z"}
    )
    updated_at: Optional[datetime] = Field(
        None, json_schema_extra={"example": "2025-01-01T13:00:00.392Z"}
    )


class InfoMixin(BaseModel):
    """Adds an optional `info` field with free-form description note to a schema."""

    info: Optional[str] = Field(
        None,
        description=("Additional description notes about the contact."),
        json_schema_extra={
            "example": (
                "Works in automotive. Met at conference in Prague 13.08.2025.\n"
                "Loves cats, allergic to nuts and cocoa."
            )
        },
    )
