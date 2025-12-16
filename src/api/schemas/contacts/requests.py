"""
Pydantic schemas for contact operations.

Includes request models.
"""

from typing import Optional
from datetime import date

from pydantic import BaseModel, EmailStr, field_validator

from src.api.schemas.validators.common import at_least_one_field_required_validator

from src.api.schemas.common.fields import EmailField
from .fields import (
    FirstNameField,
    LastNameField,
    PhoneNumberField,
    BirthdateField,
    InfoField,
)


class ContactRequestSchema(BaseModel):
    """Contact schema including optional info."""

    first_name: Optional[str] = FirstNameField(optional=True)
    last_name: Optional[str] = LastNameField(optional=True)
    email: EmailStr = EmailField()
    phone_number: str = PhoneNumberField()
    birthdate: date = BirthdateField()
    info: Optional[str] = InfoField(optional=True)

    @field_validator("birthdate")
    @classmethod
    def _birthdate_not_in_the_future(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value


@at_least_one_field_required_validator
class ContactOptionalRequestSchema(BaseModel):
    """Schema for partial contact updates. All fields optional."""

    first_name: Optional[str] = FirstNameField(optional=True)
    last_name: Optional[str] = LastNameField(optional=True)
    email: Optional[EmailStr] = EmailField(optional=True)
    phone_number: Optional[str] = PhoneNumberField(optional=True)
    birthdate: Optional[date] = BirthdateField(optional=True)
    info: Optional[str] = InfoField(optional=True)

    @field_validator("birthdate")
    @classmethod
    def _birthdate_not_in_the_future(cls, value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value


class ContactsFilterRequestSchema(BaseModel):
    """Schema for filtering contacts."""

    first_name: Optional[str] = FirstNameField(
        optional=True,
        description=(
            "Filter by first name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
    last_name: Optional[str] = LastNameField(
        optional=True,
        description=(
            "Filter by last name match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
    email: Optional[str] = EmailField(
        optional=True,
        description=(
            "Filter by e-mail match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
