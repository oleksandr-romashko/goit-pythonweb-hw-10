"""FastAPI api error responses"""

from typing import Dict, Union

from src.utils.constants import MESSAGE_ERROR_CONTACT_NOT_FOUND

from src.api.schemas.errors import (
    ImproperTokenErrorResponse,
    InvalidTokenCredentialsErrorResponse,
    UserIsInactiveErrorResponse,
    AccessDeniedErrorResponse,
    ContactNotFoundErrorResponse,
    UsernameIsReservedErrorResponse,
    ResourceAlreadyExistsDictErrorResponse,
    InternalServerErrorResponse,
)

ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES: Dict = {
    401: {
        "description": "Unauthorized - Invalid JWT token",
        "model": Union[
            ImproperTokenErrorResponse, InvalidTokenCredentialsErrorResponse
        ],
        "content": {
            "application/json": {
                "examples": {
                    "Improper token": {
                        "summary": "Example for invalid JWT token",
                        "value": ImproperTokenErrorResponse.generate_example_recursive(),
                    },
                    "Invalid credentials": {
                        "summary": "Example for invalid JWT credentials",
                        "value": InvalidTokenCredentialsErrorResponse.generate_example_recursive(),
                    },
                },
            }
        },
    },
    403: {
        "description": "Forbidden - Not active user",
        "model": UserIsInactiveErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "User is inactive": {
                        "summary": "Example for inactive user",
                        "value": UserIsInactiveErrorResponse.generate_example_recursive(),
                    },
                }
            }
        },
    },
}

ON_CURRENT_ACTIVE_ADMIN_ERRORS_RESPONSES: Dict = {
    **ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,  # inherit all 401/403 errors of a regular active user
    403: {
        "description": "Forbidden - Not active user or access denied",
        "model": Union[UserIsInactiveErrorResponse, AccessDeniedErrorResponse],
        "content": {
            "application/json": {
                "examples": {
                    "User is inactive": {
                        "summary": "Example for inactive user",
                        "value": UserIsInactiveErrorResponse.generate_example_recursive(),
                    },
                    "Access denied": {
                        "summary": "Example for access denied",
                        "value": AccessDeniedErrorResponse.generate_example_recursive(),
                    },
                }
            }
        },
    },
}

ON_CONTACT_NOT_FOUND_RESPONSE: Dict = {
    404: {
        "model": ContactNotFoundErrorResponse,
        "description": MESSAGE_ERROR_CONTACT_NOT_FOUND,
    }
}

ON_USER_REGISTER_CONFLICT_RESPONSE: Dict = {
    409: {
        "description": "Conflict - Username or email already exists, or reserved username used.",
        "model": Union[
            UsernameIsReservedErrorResponse, ResourceAlreadyExistsDictErrorResponse
        ],
        "content": {
            "application/json": {
                "examples": {
                    "User already exists": {
                        "summary": "Username or email already taken",
                        "value": ResourceAlreadyExistsDictErrorResponse.generate_example(),
                    },
                    "Reserved username": {
                        "summary": "Attempt to register reserved system username",
                        "value": UsernameIsReservedErrorResponse.generate_example(),
                    },
                },
            }
        },
    }
}

ON_INTERNAL_SERVER_ERROR_RESPONSE: Dict = {
    500: {
        "model": InternalServerErrorResponse,
        "description": (
            "Database is not configured correctly "
            "or error connecting to the database"
        ),
    },
}
