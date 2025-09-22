"""
Pydantic schemas for contact operations.

Includes request/response models for creating, updating,
and retrieving contacts, plus models for special responses.
"""

from typing import Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator


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


class BaseORMModel(BaseModel):
    """Base schema with ORM support via `from_attributes`.

    Adds reading the instance attributes corresponding to the model field names.
    Provides integration with object-relational mappings (ORMs).
    """

    model_config = ConfigDict(from_attributes=True)


class InfoMixin(BaseModel):
    """Adds an optional `info` field with free-form notes to a schema."""

    info: Optional[str] = Field(
        None,
        description=(
            "Additional notes about the contact (preferences, allergies, etc.)."
        ),
        json_schema_extra={
            "example": (
                "Works in automotive. Met at conference in Prague 13.08.2025.\n"
                "Loves cats, allergic to nuts and cocoa."
            )
        },
    )


class ContactBaseRequiredSchema(BaseModel):
    """Required fields common to all contacts."""

    first_name: str = Field(
        description="First name", max_length=50, json_schema_extra={"example": "John"}
    )
    last_name: str = Field(
        description="Last name",
        max_length=50,
        json_schema_extra={"example": "Doe"},
    )
    email: EmailStr = Field(
        description="E-mail address",
        max_length=150,
        json_schema_extra={"example": "john.doe@gmail.com"},
    )
    phone_number: str = Field(
        description="Phone number",
        max_length=40,
        json_schema_extra={"example": "+420123456789"},
    )
    birthdate: date = Field(
        description="Birthday date",
        json_schema_extra={"example": date(2000, 1, 4).isoformat()},
    )

    @field_validator("birthdate")
    def check_birthdate_not_in_future(  # pylint: disable=no-self-argument
        cls, value: date
    ) -> date:
        """Performs check if birthday is in the past or today"""
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value


class ContactModelSchema(InfoMixin, ContactBaseRequiredSchema):
    """Full contact schema including optional notes."""


class ContactResponseSchema(BaseORMModel, TimestampsMixin, ContactModelSchema, IdMixin):
    """Schema for returning a contact in API responses."""


class ContactCelebrationResponseSchema(BaseORMModel, ContactModelSchema, IdMixin):
    """Schema for contacts with upcoming birthday celebrations."""

    celebration_date: date = Field(
        description="Actual celebration date",
        json_schema_extra={"example": date(2025, 1, 6).isoformat()},
    )


class ContactPartialUpdateSchema(InfoMixin, BaseModel):
    """Schema for partial contact updates. All fields optional."""

    first_name: Optional[str] = Field(
        None,
        description="First name",
        max_length=50,
        json_schema_extra={"example": "John"},
    )
    last_name: Optional[str] = Field(
        None,
        description="Last name",
        max_length=50,
        json_schema_extra={"example": "Doe"},
    )
    email: Optional[EmailStr] = Field(
        None,
        description="E-mail address",
        max_length=150,
        json_schema_extra={"example": "john.doe@gmail.com"},
    )
    phone_number: Optional[str] = Field(
        None,
        description="Phone number",
        max_length=40,
        json_schema_extra={"example": "+420123456789"},
    )
    birthdate: Optional[date] = Field(
        None,
        description="Birthday date",
        json_schema_extra={"example": date(2000, 1, 4).isoformat()},
    )

    @field_validator("birthdate")
    def check_birthdate_not_in_future(  # pylint: disable=no-self-argument
        cls, value: date
    ) -> date:
        """Performs check if birthday is in the past or today"""
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value
