"""FastAPI api successful responses"""

from typing import Dict

from src.api.schemas.users.responses import (
    UserAboutMeOneOfResponseSchema,
    UserAboutMeResponseSchema,
    UserAboutMeAdminResponseSchema,
)

ON_ME_SUCCESS_RESPONSE: Dict = {
    200: {
        "description": (
            "Regular User or Admin response "
            "on successfully retrieved current user information."
        ),
        "model": UserAboutMeOneOfResponseSchema,
        "content": {
            "application/json": {
                "examples": {
                    "Regular user": {
                        "summary": "Example for regular user",
                        "value": UserAboutMeResponseSchema.generate_example_recursive(),
                    },
                    "Admin user": {
                        "summary": "Example for admin user",
                        "value": UserAboutMeAdminResponseSchema.generate_example_recursive(),
                    },
                }
            }
        },
    },
}
