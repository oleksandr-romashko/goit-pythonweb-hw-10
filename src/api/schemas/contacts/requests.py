"""
Pydantic schemas for contact operations.

Includes request models.
"""

from typing import Optional
from datetime import date

from pydantic import BaseModel, EmailStr

from src.api.schemas.validators.common import at_least_one_field_required_validator
from src.api.schemas.validators.contacts import birthdate_not_in_the_future_validator

from src.api.schemas.common.fields import EmailField
from .fields import (
    FirstNameField,
    LastNameField,
    PhoneNumberField,
    BirthdateField,
    InfoField,
)


@birthdate_not_in_the_future_validator
class ContactRequestSchema(BaseModel):
    """Contact schema including optional info."""

    first_name: Optional[str] = FirstNameField(optional=True)
    last_name: Optional[str] = LastNameField(optional=True)
    email: EmailStr = EmailField()
    phone_number: str = PhoneNumberField()
    birthdate: date = BirthdateField()
    info: Optional[str] = InfoField(optional=True)


@at_least_one_field_required_validator
@birthdate_not_in_the_future_validator
class ContactOptionalRequestSchema(BaseModel):
    """Schema for partial contact updates. All fields optional."""

    first_name: Optional[str] = FirstNameField(optional=True)
    last_name: Optional[str] = LastNameField(optional=True)
    email: Optional[EmailStr] = EmailField(optional=True)
    phone_number: Optional[str] = PhoneNumberField(optional=True)
    birthdate: Optional[date] = BirthdateField(optional=True)
    info: Optional[str] = InfoField(optional=True)


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
    email: Optional[EmailStr] = EmailField(
        optional=True,
        description=(
            "Filter by e-mail match "
            "(optional parameter, case-insensitive partial match search)"
        ),
    )
