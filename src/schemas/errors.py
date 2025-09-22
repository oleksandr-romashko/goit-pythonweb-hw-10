"""Pydantic schemas describing standard error responses."""

from pydantic import BaseModel, Field
from src.utils.constants import (
    MESSAGE_ERROR_CONTACT_NOT_FOUND,
    MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS,
    MESSAGE_ERROR_INTERNAL_SERVER_ERROR,
)


class ContactNotFoundErrorResponse(BaseModel):
    """Error for 404 Not Found when a contact is missing."""

    detail: str = Field(json_schema_extra={"example": MESSAGE_ERROR_CONTACT_NOT_FOUND})


class ResourceAlreadyExistsErrorResponse(BaseModel):
    """Error for 409 Conflict when a resource already exists."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS}
    )


class InternalServerErrorResponse(BaseModel):
    """Error for generic 5xx server issues."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INTERNAL_SERVER_ERROR}
    )
