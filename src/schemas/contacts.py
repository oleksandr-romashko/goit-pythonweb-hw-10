"""
Pydantic schemas for contact operations.

Includes request/response models for creating, updating,
and retrieving contacts, plus models for special responses.
"""

from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, EmailStr, field_validator

from .mixins import BaseORMModel, IdMixin, InfoMixin, TimestampsMixin


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

    contact_id: Optional[int] = None

    @field_validator("birthdate")
    def check_birthdate_not_in_future(  # pylint: disable=no-self-argument
        cls, value: date
    ) -> date:
        """Performs check if birthday is in the past or today"""
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value


class ContactModelSchema(InfoMixin, ContactBaseRequiredSchema):
    """Full contact schema including optional info."""


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


class ContactsFilterSchema(BaseModel):
    """Schema for filtering contacts."""

    first_name: Optional[str] = Field(
        None,
        description=(
            "Filter by first name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
        max_length=50,
        json_schema_extra={"example": "John"},
    )
    last_name: Optional[str] = Field(
        None,
        description=(
            "Filter by last name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
        max_length=50,
        json_schema_extra={"example": "Doe"},
    )
    email: Optional[EmailStr] = Field(
        None,
        description=(
            "Filter by e-mail match "
            "(optional parameter, case-insensitive partial match search)"
        ),
        max_length=150,
        json_schema_extra={"example": "john.doe@gmail.com"},
    )


async def get_contacts_query_filter(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
) -> ContactsFilterSchema:
    """Dependency provider for contacts filter."""
    return ContactsFilterSchema(first_name=first_name, last_name=last_name, email=email)
