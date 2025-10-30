"""Common validators for Pydantic schemas."""

from typing import Type

from pydantic import BaseModel, model_validator

from src.api.errors.http_errors import raise_http_400_error
from src.utils.constants import MESSAGE_ERROR_BAD_REQUEST_EMPTY


def at_least_one_field_required_validator(cls: Type[BaseModel]) -> Type[BaseModel]:
    """
    Class decorator for Pydantic models.
    Ensures that at least one field has a non-None value.
    Returns a new subclass with the validator applied.
    """

    class Wrapper(cls):
        """Wrapped class with added validation method"""

        @model_validator(mode="before")
        @classmethod
        def _check_at_least_one_field(cls, values):
            if not any(value is not None for value in values.values()):
                raise_http_400_error(MESSAGE_ERROR_BAD_REQUEST_EMPTY)
            return values

    return Wrapper
