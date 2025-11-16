"""Validators for Pydantic schemas for contacts operations."""

from typing import Type, Optional
from datetime import date

from pydantic import BaseModel, field_validator


# def birthdate_not_in_the_future_validator(cls: Type[BaseModel]) -> Type[BaseModel]:
#     """Decorator adding birthday field validation"""

#     class Wrapped(cls):
#         """Validate birthdate"""

#         @field_validator("birthdate")
#         @classmethod
#         def _check_birthdate_not_in_future(cls, value: Optional[date]) -> date | None:
#             """Performs check if birthday is in the past or today"""
#             if value is None:
#                 return value
#             if value > date.today():
#                 raise ValueError("Birthdate cannot be in the future")
#             return value

#     return Wrapped


def birthdate_not_in_the_future_validator(
    model_cls: Type[BaseModel],
) -> Type[BaseModel]:
    """Adds field validator for birthdate to prevent future dates."""

    @field_validator("birthdate")
    def _check(value: Optional[date]) -> Optional[date]:
        if value is None:
            return value
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value

    setattr(model_cls, "_check_birthdate_not_in_future", _check)
    model_cls.model_rebuild(force=True)

    return model_cls
