"""Pydantic schemas describing standard error responses."""

from pydantic import BaseModel, Field


from src.utils.constants import (
    MESSAGE_ERROR_BAD_REQUEST_EMPTY,
    MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN,
    MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED,
    MESSAGE_ERROR_NOT_AUTHENTICATED,
    MESSAGE_ERROR_INVALID_OR_EXPIRED_AUTH_TOKEN,
    MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS,
    MESSAGE_ERROR_EMAIL_VERIFICATION_REQUIRED,
    MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS,
    MESSAGE_ERROR_ACCESS_DENIED,
    MESSAGE_ERROR_INACTIVE_USER,
    MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED,
    MESSAGE_ERROR_CONTACT_NOT_FOUND,
    MESSAGE_ERROR_RESOURCE_ALREADY_EXISTS,
    MESSAGE_ERROR_INTERNAL_SERVER_ERROR,
    MESSAGE_ERROR_SERVER_ERROR_NOT_IMPLEMENTED,
    MESSAGE_ERROR_USERNAME_IS_RESERVED,
)

from .mixins import ExampleGenerationMixin


class ErrorResponse(ExampleGenerationMixin, BaseModel):
    """Common error parent."""


class BadEmptyValuesRequestErrorResponse(ErrorResponse):
    """Error for 400 Bad Request when no values are provided for the update."""

    detail: str = Field(
        json_schema_extra={
            "example": MESSAGE_ERROR_BAD_REQUEST_EMPTY,
        },
    )


class InvalidTokenRequestErrorResponse(ErrorResponse):
    """Error for 400 Bad Request when token is invalid."""

    detail: str = Field(
        json_schema_extra={
            "example": MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN,
        },
    )


class EmailIsVerifiedErrorResponse(ErrorResponse):
    """Error for 400 Bad Request when email is verified before."""

    detail: str = Field(
        json_schema_extra={
            "example": MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED,
        },
    )


class BadMePasswordUpdateValuesRequestErrorResponse(ErrorResponse):
    """
    Error for 400 Bad Request when provided update values for password update are incorrect or improper.
    """

    detail: str = Field(
        json_schema_extra={
            "example": {
                "old_password": "Old password is required to change password",
                "new_password": "New password can't be empty",
            },
        },
    )


class InvalidAuthErrorResponse(ErrorResponse):
    """General error for 401 Unauthorized."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_NOT_AUTHENTICATED},
    )


class ImproperAuthTokenErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when a JWT token can't be processed."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INVALID_OR_EXPIRED_AUTH_TOKEN},
    )


class InvalidTokenCredentialsErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when a JWT token has invalid credentials."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INVALID_TOKEN_AUTH_CREDENTIALS},
    )


class InvalidLoginCredentialsErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when user login failed due to invalid credentials."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS}
    )


class EmailNotVerifiedErrorResponse(ErrorResponse):
    """Error for 401 Unauthorized when login failed because user email is not verified."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_EMAIL_VERIFICATION_REQUIRED}
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


class AccessDeniedInvalidRoleErrorResponse(ErrorResponse):
    """Error for 403 Forbidden when access denied due to invalid role."""

    detail: str = Field(
        json_schema_extra={
            "example": f"{MESSAGE_ERROR_SERVER_ERROR_NOT_IMPLEMENTED}: <details message>"
        },
    )


class ContactNotFoundErrorResponse(ErrorResponse):
    """Error for 404 Not Found when a contact is missing."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_CONTACT_NOT_FOUND},
    )


class UserNotFoundErrorResponse(ErrorResponse):
    """Error for 404 Not Found when a user is missing."""

    detail: str = Field(
        json_schema_extra={
            "example": MESSAGE_ERROR_USER_NOT_FOUND_OR_ACTION_IS_NOT_ALLOWED
        },
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


class NotImplementedServerErrorResponse(ErrorResponse):
    """Error for 501 Not Implemented Yet server issue."""

    detail: str = Field(
        json_schema_extra={"example": MESSAGE_ERROR_SERVER_ERROR_NOT_IMPLEMENTED}
    )
