"""Pydantic schemas describing standard error responses."""

from pydantic import BaseModel, Field


from src.utils.constants import (
    MESSAGE_ERROR_NOT_AUTHENTICATED,
    MESSAGE_ERROR_INVALID_AUTH_TOKEN,
    MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS,
    MESSAGE_ERROR_INACTIVE_USER,
    MESSAGE_ERROR_ACCESS_DENIED,
    MESSAGE_ERROR_CONTACT_NOT_FOUND,
    MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS,
    MESSAGE_ERROR_INTERNAL_SERVER_ERROR,
    MESSAGE_ERROR_USERNAME_IS_RESERVED,
)

from .mixins import ExampleMixin


class ErrorResponse(ExampleMixin, BaseModel):
    """Common error parent."""


class InvalidAuthErrorResponse(ErrorResponse):
    """General error for 401 Unauthorized."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_NOT_AUTHENTICATED},
    )


class ImproperTokenErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when a JWT token can't be processed."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INVALID_AUTH_TOKEN},
    )


class InvalidTokenCredentialsErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when a JWT token has invalid credentials."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS},
    )


class UserIsInactiveErrorResponse(ErrorResponse):
    """Error for 403 Forbidden when user is inactive."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INACTIVE_USER},
    )


class AccessDeniedErrorResponse(ErrorResponse):
    """Error for 403 Forbidden when access denied."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_ACCESS_DENIED},
    )


class ContactNotFoundErrorResponse(ErrorResponse):
    """Error for 404 Not Found when a contact is missing."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_CONTACT_NOT_FOUND},
    )


class ResourceAlreadyExistsStrErrorResponse(ErrorResponse):
    """Error for 409 Conflict when a resource already exists."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS}
    )


class ResourceAlreadyExistsDictErrorResponse(ErrorResponse):
    """Error for 409 Conflict when a resource already exists."""

    detail: str = Field(
        json_schema_extra={
            "example": {
                "username": "Username is already taken.",
                "email": "User with such Email is already registered.",
            }
        }
    )


class UsernameIsReservedErrorResponse(ErrorResponse):
    """Error for 409 Conflict when a username is reserved and can't be used."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_USERNAME_IS_RESERVED}
    )


class InternalServerErrorResponse(ErrorResponse):
    """Error for generic 5xx server issues."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INTERNAL_SERVER_ERROR}
    )
