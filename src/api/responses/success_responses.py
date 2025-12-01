"""FastAPI api successful responses"""

from typing import Dict

from src.utils.constants import (
    MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT,
    MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED,
)

from src.api.schemas.auth.responses import EmailVerificationSuccessResponseSchema
from src.api.schemas.users.responses import (
    UserAboutMeOneOfResponseSchema,
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
    UserAdminRegisteredUserResponseSchema,
)

ON_RESEND_VERIFICATION_EMAIL_RESPONSE: Dict = {
    200: {
        "description": "Result of attempting to resend verification email.",
        "content": {
            "application/json": {
                "examples": {
                    "Verification email sent": {
                        "summary": "Email exists and needs verification.",
                        "value": {"details": MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT},
                    },
                    "Email already verified": {
                        "summary": "User email is already verified.",
                        "value": {
                            "details": MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED
                        },
                    },
                    "Non existing user masked": {
                        "summary": (
                            "Email not found, but masked as success "
                            "(security best practice)."
                        ),
                        "description": (
                            "Used to avoid leaking which emails exist in the system."
                        ),
                        "value": {"details": MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT},
                    },
                }
            }
        },
    },
}

ON_VERIFIED_EMAIL_SUCCESS_RESPONSE: Dict = {
    200: {
        "description": "Response on successfully verified user email.",
        "model": EmailVerificationSuccessResponseSchema,
    },
}


ON_ME_SUCCESS_RESPONSE: Dict = {
    200: {
        "description": "Response on successfully retrieved current user information.",
        "model": UserAboutMeOneOfResponseSchema,
        "content": {
            "application/json": {
                "examples": {
                    "Regular user": {
                        "summary": "Example for regular user",
                        "value": UserAboutMeResponseSchema.generate_example_recursive(),
                    },
                    "Admin user": {
                        "summary": "Example for entrusted users (Moderator, Admin, Superadmin)",
                        "value": UserAboutMeAdminResponseSchema.generate_example_recursive(),
                    },
                }
            }
        },
    },
}


on_get_user_admin_other_admin_example = (
    UserAdminRegisteredUserResponseSchema.generate_example_recursive()
)
for field in ("contacts_count", "created_at", "updated_at", "is_active"):
    on_get_user_admin_other_admin_example.pop(field, None)

on_get_user_admin_self_example = (
    UserAdminRegisteredUserResponseSchema.generate_example_recursive()
)
on_get_user_admin_self_example.update({"role": "admin"})

on_get_user_superadmin_admin_example = (
    UserAdminRegisteredUserResponseSchema.generate_example_recursive()
)
on_get_user_superadmin_admin_example.update({"role": "admin"})

on_get_user_superadmin_self_example = (
    UserAdminRegisteredUserResponseSchema.generate_example_recursive()
)
on_get_user_superadmin_self_example.update({"role": "superadmin"})

ON_GET_USER_BY_ID_SUCCESS_RESPONSE: Dict = {
    200: {
        "description": (
            "Regular User or Admin response "
            "on successfully retrieved current user information."
        ),
        "model": UserAdminRegisteredUserResponseSchema,
        "content": {
            "application/json": {
                "examples": {
                    "Admin user getting regular user data": {
                        "summary": "Example for ADMIN user getting regular USER data",
                        "value": UserAdminRegisteredUserResponseSchema.generate_example_recursive(),
                    },
                    "Admin user getting other admin data": {
                        "summary": "Example for ADMIN user getting other ADMIN data",
                        "value": on_get_user_admin_other_admin_example,
                    },
                    "Admin user getting self data": {
                        "summary": "Example for ADMIN user getting SELF user data",
                        "value": on_get_user_admin_self_example,
                    },
                    "Superadmin user getting regular user data": {
                        "summary": "Example for SUPERADMIN user getting regular USER data",
                        "value": UserAdminRegisteredUserResponseSchema.generate_example_recursive(),
                    },
                    "Superadmin user getting active admin user data": {
                        "summary": "Example for SUPERADMIN user getting active ADMIN user data",
                        "value": on_get_user_superadmin_admin_example,
                    },
                    "Superadmin user getting self data": {
                        "summary": "Example for SUPERADMIN user getting SELF user data",
                        "value": on_get_user_superadmin_self_example,
                    },
                }
            }
        },
    },
}

ON_VERIFIED_EMAIL_SUCCESS_RESPONSE_WITH_REDIRECT: Dict = {
    302: {
        "description": (
            "Response on successfully verified user email with redirect.\n\n"
            "E.g. redirect to *https://frontend.example.com/email-verified*"
        ),
        "headers": {
            "Location": {
                "description": "URL to which the client will be redirected",
                "schema": {"type": "string"},
            }
        },
        "content": None,
    },
}
