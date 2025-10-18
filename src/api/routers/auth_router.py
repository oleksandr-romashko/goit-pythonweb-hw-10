"""
Auth API endpoints.

Provides operations for user registration and authentication.
"""

from fastapi import APIRouter, Depends, status, Response
from fastapi.security import OAuth2PasswordRequestForm

from src.config import app_config
from src.db.models import User
from src.services import AuthService, UserService, ContactService
from src.services.errors import UserConflictError, InvalidUserCredentialsError
from src.utils.constants import (
    MESSAGE_ERROR_USERNAME_IS_RESERVED,
    MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS,
)
from src.utils.logger import logger


from src.api.dependencies import (
    get_auth_service,
    get_user_service,
    get_contacts_service,
)
from src.api.errors import raise_http_401_error, raise_http_409_error
from src.api.responses.error_responses import ON_USER_REGISTER_CONFLICT_RESPONSE
from src.api.schemas.auth import AccessTokenResponseSchema
from src.api.schemas.users import (
    UserRegisterRequestSchema,
    UserLoginRequestSchema,
    UserRegisteredResponseSchema,
)

router = APIRouter(prefix="/auth", tags=["Auth (Public Access)"])


@router.post(
    "/register",
    summary="Public user registration",
    description=(
        "Create a new user by anonymous user.\n\n"
        "User should have unique `username`, `e-mail`, and strong password.\n\n"
        "There are  some ***reserved usernames*** that are not allowed to create user with: "
        f"{', '.join([f'_{name}_' for name in app_config.RESERVED_USERNAMES])}."
    ),
    response_model=UserRegisteredResponseSchema,
    status_code=status.HTTP_201_CREATED,
    response_description="Successfully registered a new user.",
    responses={
        **ON_USER_REGISTER_CONFLICT_RESPONSE,
    },
)
async def register_user(
    body: UserRegisterRequestSchema,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
) -> UserRegisteredResponseSchema:
    """Create a new user."""

    # Check for reserved names
    if body.username.lower() in app_config.effective_reserved_usernames:
        raise_http_409_error(MESSAGE_ERROR_USERNAME_IS_RESERVED)

    try:
        user: User = await user_service.create_user(
            body.username, body.email, body.password
        )
    except UserConflictError as exc:
        logger.info(exc)
        raise_http_409_error(detail=exc.errors)

    data = UserRegisteredResponseSchema.model_validate(user)

    # Add number of user contacts
    data.contacts_count = await contacts_service.get_contacts_count(user.id)

    logger.info(
        "Created a new user with id = %s and username '%s'.", user.id, user.username
    )
    response.headers["Location"] = "api/users/me"
    return data


@router.post(
    "/login",
    summary="User login",
    description=(
        "Authenticate user based on `username` and `password` in the request body "
        "and return a valid JWT access token."
    ),
    response_model=AccessTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully authenticated user.",
)
async def login_user(
    body: UserLoginRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> AccessTokenResponseSchema:
    """Validate user credentials using request body and issue access token."""
    return await _authenticate_and_issue_token(
        body.username, body.password, auth_service, user_service
    )


@router.post(
    "/oauth2-login",
    summary="OAuth2 scheme user login",
    description=(
        "Authenticate user based on OAuth2 login scheme "
        "and return a valid JWT access token."
    ),
    response_model=AccessTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully authenticated user.",
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> AccessTokenResponseSchema:
    """Validate user credentials using OAuth2 scheme and issue access token."""
    return await _authenticate_and_issue_token(
        form_data.username, form_data.password, auth_service, user_service
    )


async def _authenticate_and_issue_token(
    username: str,
    password: str,
    auth_service: AuthService,
    user_service: UserService,
) -> AccessTokenResponseSchema:
    """Process user credentials and issue access token"""
    # Check user credentials
    try:
        user: User = await user_service.validate_user_credentials(username, password)
    except InvalidUserCredentialsError as exc:
        logger.warning(
            "Failed login attempt: Not valid credentials for username '%s': %s",
            username,
            str(exc),
        )
        raise_http_401_error(MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS)

    # Generate access token
    token = auth_service.create_access_token(user.id)

    logger.info(
        "Issued access token to user with username '%s' after login authentication.",
        user.username,
    )
    return AccessTokenResponseSchema(
        access_token=token,
        token_type="bearer",
    )
