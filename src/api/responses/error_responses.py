"""FastAPI api error responses"""

from typing import Dict, Union

from src.utils.constants import (
    MESSAGE_ERROR_DB_INVALID_CONFIG,
    MESSAGE_ERROR_BAD_REQUEST,
    MESSAGE_ERROR_CONTACT_NOT_FOUND,
    MESSAGE_ERROR_USER_NOT_FOUND,
    MESSAGE_ERROR_USER_VIEW_IS_RESTRICTED,
    MESSAGE_ERROR_USER_DELETION_IS_RESTRICTED,
    MESSAGE_ERROR_FEATURE_IS_PLANNED,
)

from src.api.schemas.errors import (
    ImproperTokenErrorResponse,
    InvalidTokenCredentialsErrorResponse,
    InvalidLoginCredentialsErrorResponse,
    EmailNotVerifiedErrorResponse,
    UserIsInactiveErrorResponse,
    BadEmptyValuesRequestErrorResponse,
    InvalidTokenRequestErrorResponse,
    EmailIsVerifiedErrorResponse,
    BadMeValuesRequestErrorResponse,
    AccessDeniedErrorResponse,
    AccessDeniedInvalidRoleErrorResponse,
    ContactNotFoundErrorResponse,
    UserNotFoundErrorResponse,
    UsernameIsReservedErrorResponse,
    ResourceAlreadyExistsDictErrorResponse,
    InternalServerErrorResponse,
    NotImplementedServerErrorResponse,
)

ON_UPDATE_EMPTY_BAD_REQUEST_RESPONSE: Dict = {
    400: {
        "description": MESSAGE_ERROR_BAD_REQUEST,
        "model": BadEmptyValuesRequestErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "Body is empty": {
                        "summary": "At least one field is required",
                        "value": BadEmptyValuesRequestErrorResponse.generate_example_recursive(),
                    },
                },
            }
        },
    },
}

ON_VERIFY_EMAIL_BAD_REQUEST_RESPONSE: Dict = {
    400: {
        "description": MESSAGE_ERROR_BAD_REQUEST,
        "model": Union[InvalidTokenRequestErrorResponse, EmailIsVerifiedErrorResponse],
        "content": {
            "application/json": {
                "examples": {
                    "Invalid token": {
                        "summary": "Invalid token",
                        "value": InvalidTokenRequestErrorResponse.generate_example_recursive(),
                    },
                    "Email is already verified": {
                        "summary": "Email is already verified",
                        "value": EmailIsVerifiedErrorResponse.generate_example_recursive(),
                    },
                },
            }
        },
    },
}

ON_ME_UPDATE_BAD_REQUEST_RESPONSE_EMPTY_AND_BAD_VALUES: Dict = {
    400: {
        "description": MESSAGE_ERROR_BAD_REQUEST,
        "model": Union[
            BadEmptyValuesRequestErrorResponse, BadMeValuesRequestErrorResponse
        ],
        "content": {
            "application/json": {
                "examples": {
                    "Body is empty": {
                        "summary": "At least one field is required",
                        "value": BadEmptyValuesRequestErrorResponse.generate_example_recursive(),
                    },
                    "Bad request values": {
                        "summary": "Combined details on bad password and email fields",
                        "value": BadMeValuesRequestErrorResponse.generate_example_recursive(),
                    },
                },
            }
        },
    },
}


ON_LOGIN_USER_ERRORS_RESPONSES: Dict = {
    401: {
        "description": "Unauthorized - invalid login credentials or unverified email",
        "model": Union[
            InvalidLoginCredentialsErrorResponse, EmailNotVerifiedErrorResponse
        ],
        "content": {
            "application/json": {
                "examples": {
                    "Invalid credentials": {
                        "summary": "Invalid username or password",
                        "value": InvalidLoginCredentialsErrorResponse.generate_example_recursive(),
                    },
                    "Email not verified": {
                        "summary": "Email verification required",
                        "value": EmailNotVerifiedErrorResponse.generate_example_recursive(),
                    },
                },
            }
        },
    },
}

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
    **ON_CURRENT_ACTIVE_USER_ERRORS_RESPONSES,  # inherit 401/403 errors of a regular active user
    403: {
        "description": "Forbidden - Not active user or access denied",
        "model": AccessDeniedErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "Access denied": {
                        "summary": "Example for access denied",
                        "value": AccessDeniedErrorResponse.generate_example_recursive(),
                    },
                }
            }
        },
    },
}

ON_USER_FORBIDDEN_OR_ROLE_IS_INVALID_RESPONSE: Dict = {
    403: {
        "description": "Forbidden - Role is invalid or access denied",
        "model": Union[
            AccessDeniedErrorResponse,
            AccessDeniedInvalidRoleErrorResponse,
        ],
        "content": {
            "application/json": {
                "examples": {
                    "Access denied": {
                        "summary": "Example for access denied",
                        "value": AccessDeniedErrorResponse.generate_example_recursive(),
                    },
                    "User role is invalid": {
                        "summary": "Example for user role is invalid",
                        "value": AccessDeniedInvalidRoleErrorResponse.generate_example_recursive(),
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

ON_USER_NOT_FOUND_OR_VIEW_RESTRICTED_RESPONSE: Dict = {
    404: {
        "model": UserNotFoundErrorResponse,
        "description": f"{MESSAGE_ERROR_USER_NOT_FOUND} or {MESSAGE_ERROR_USER_VIEW_IS_RESTRICTED}",
    }
}

ON_USER_NOT_FOUND_OR_DELETE_RESTRICTED_RESPONSE: Dict = {
    404: {
        "model": UserNotFoundErrorResponse,
        "description": (
            f"{MESSAGE_ERROR_USER_NOT_FOUND} "
            f"or {MESSAGE_ERROR_USER_DELETION_IS_RESTRICTED}"
        ),
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
        "description": f"{MESSAGE_ERROR_DB_INVALID_CONFIG} or error connecting to the database",
    },
}

ON_NOT_IMPLEMENTED_SERVER_ERROR_RESPONSE: Dict = {
    501: {
        "model": NotImplementedServerErrorResponse,
        "description": MESSAGE_ERROR_FEATURE_IS_PLANNED,
    },
}
