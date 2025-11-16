"""Common validators for Pydantic schemas."""

from typing import Type

from pydantic import BaseModel, model_validator

from src.api.errors.http_errors import raise_http_400_error
from src.utils.constants import MESSAGE_ERROR_BAD_REQUEST_EMPTY


def at_least_one_field_required_validator(
    model_cls: Type[BaseModel],
) -> Type[BaseModel]:
    """Adds validator ensuring that at least one field is not None."""

    @model_validator(mode="before")
    def _check(values):
        if not any(value is not None for value in values.values()):
            raise_http_400_error(MESSAGE_ERROR_BAD_REQUEST_EMPTY)
        return values

    setattr(model_cls, "_check_at_least_one_field", _check)
    model_cls.model_rebuild(force=True)

    return model_cls
