"""
Pydantic schemas for contact operations.

Includes request/response models for creating, updating,
and retrieving contacts, plus models for special responses.
"""

from datetime import date

from pydantic import BaseModel, EmailStr

from src.api.schemas.mixins import FromOrmAttributesConfig, IdMixin, TimestampsMixin

from .fields import (
    FirstNameField,
    LastNameField,
    EmailField,
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
