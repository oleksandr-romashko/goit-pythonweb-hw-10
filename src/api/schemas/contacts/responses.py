"""
Pydantic schemas for contact operations.

Includes response models.
"""

from datetime import date

from pydantic import BaseModel, EmailStr

from src.api.schemas.mixins import FromOrmAttributesConfig, IdMixin, TimestampsMixin

from src.api.schemas.common.fields import EmailField
from .fields import (
    FirstNameField,
    LastNameField,
    PhoneNumberField,
    BirthdateField,
    InfoField,
    CelebrationDateField,
)


class ContactResponseSchema(
    TimestampsMixin, IdMixin, FromOrmAttributesConfig, BaseModel
):
    """Schema for returning a contact in API responses."""

    first_name: str = FirstNameField(validate=False)
    last_name: str = LastNameField(validate=False)
    email: EmailStr = EmailField(validate=False)
    phone_number: str = PhoneNumberField(validate=False)
    birthdate: date = BirthdateField()
    info: str = InfoField()


class ContactCelebrationResponseSchema(ContactResponseSchema):
    """Schema for contacts with upcoming birthday celebrations."""

    celebration_date: date = CelebrationDateField()
