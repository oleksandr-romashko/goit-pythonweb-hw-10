"""
Auth API endpoints.

Provides operations for user registration and authentication.
"""

from typing import Optional, Dict

from fastapi import (
    APIRouter,
    Depends,
    status,
    Request,
    Query,
    Response,
    BackgroundTasks,
)
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.status import HTTP_302_FOUND

from src.config import app_config
from src.db.models.enums import UserRole
from src.services import AuthService, UserService, ContactService, MailService
from src.services.dtos import UserDTO
from src.services.errors import (
    UserInactiveError,
    UserConflictError,
    InvalidUserCredentialsError,
    UserEmailIsAlreadyConfirmedError,
    InvalidTokenError,
)
from src.utils.constants import (
    MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT,
    MESSAGE_SUCCESS_EMAIL_VERIFIED,
    MESSAGE_ERROR_USERNAME_IS_RESERVED,
    MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS,
    MESSAGE_ERROR_INVALID_OR_EXPIRED_REFRESH_TOKEN,
    MESSAGE_ERROR_EMAIL_VERIFICATION_REQUIRED,
    MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED,
    MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN,
)
from src.utils.logger import logger


from src.api.dependencies import (
    get_auth_service,
    get_contacts_service,
    get_mail_service,
    get_user_service,
)
from src.api.errors import (
    raise_http_400_error,
    raise_http_401_error,
    raise_http_403_error,
    raise_http_409_error,
)
from src.api.responses.success_responses import (
    ON_VERIFIED_EMAIL_SUCCESS_RESPONSE,
    ON_VERIFIED_EMAIL_SUCCESS_RESPONSE_WITH_REDIRECT,
    ON_RESEND_VERIFICATION_EMAIL_RESPONSE,
)
from src.api.responses.error_responses import (
    ON_USER_REGISTER_CONFLICT_RESPONSE,
    ON_VERIFY_EMAIL_BAD_REQUEST_RESPONSE,
    ON_LOGIN_USER_ERRORS_RESPONSES,
)
from src.api.schemas.auth.requests import EmailRequestSchema, RefreshTokenRequestSchema
from src.api.schemas.auth.responses import (
    AccessTokenResponseSchema,
    LoginTokenResponseSchema,
)
from src.api.schemas.users.requests import (
    UserRegisterRequestSchema,
    UserLoginRequestSchema,
)
from src.api.schemas.users.responses import UserRegisteredResponseSchema
from src.api.workflows import send_verification_email

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
    responses={**ON_USER_REGISTER_CONFLICT_RESPONSE},
)
async def register_user(
    body: UserRegisterRequestSchema,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service),
    contacts_service: ContactService = Depends(get_contacts_service),
    auth_service: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
) -> UserRegisteredResponseSchema:
    """Create a new user."""

    # TODO: Add check for names, that are similar to reserved usernames (e.g. "admin1", "super_admin", etc.)
    # Check for restricted reserved user names
    if body.username.lower() in app_config.effective_reserved_usernames:
        raise_http_409_error(MESSAGE_ERROR_USERNAME_IS_RESERVED)

    # Create a new user in the database
    try:
        user: UserDTO = await user_service.register_user(
            body.username, body.email, body.password
        )
        logger.info(
            "Created a new USER with user_id = %s and username '%s'.",
            user.id,
            user.username,
        )
    except UserConflictError as exc:
        logger.info(exc)
        raise_http_409_error(detail=exc.errors)

    # Prepare response data
    response.headers["Location"] = "/api/users/me"
    data = UserRegisteredResponseSchema.model_validate(user)

    # Add number of user contacts to the response
    data.contacts_count = await contacts_service.get_contacts_count(user.id)

    # Send email verification email
    send_verification_email(
        target_user=user,
        base_url=str(request.base_url),
        auth_service=auth_service,
        mail_service=mail_service,
        background_tasks=background_tasks,
    )

    return data


@router.post(
    "/resend-verification-email",
    summary="Resend verification email",
    description="Send a verification email to the provided email address.",
    response_description="Successfully sent verification email.",
    responses={**ON_RESEND_VERIFICATION_EMAIL_RESPONSE},
)
async def resend_verification_email(
    body: EmailRequestSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
    mail_service: MailService = Depends(get_mail_service),
) -> Dict[str, str]:
    """Resend verification email to the user email address."""
    # Check user existence
    user: Optional[UserDTO] = await user_service.get_user_by_email(body.email)
    if not user:
        # Security best practice: don't reveal whether the email exists.
        logger.info(
            "Attempt to resend verification email to a non-existing user email: %s",
            body.email,
        )
        return {"details": MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT}

    # Check if user email is confirmed already
    if user.is_email_confirmed:
        logger.debug(
            "Can't resend verification email for user whose email is already verified: %s",
            user,
        )
        raise_http_400_error(MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED)

    # Send email verification email
    send_verification_email(
        target_user=user,
        base_url=str(request.base_url),
        auth_service=auth_service,
        mail_service=mail_service,
        background_tasks=background_tasks,
    )

    return {"details": MESSAGE_SUCCESS_CONFIRMATION_EMAIL_SENT}


@router.post(
    "/login",
    summary="User login",
    description=(
        "Authenticate user based on `username` and `password` in the request body "
        "and return a valid JWT auth tokens."
    ),
    response_model=LoginTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully authenticated user.",
    responses={**ON_LOGIN_USER_ERRORS_RESPONSES},
)
async def login_user(
    body: UserLoginRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> LoginTokenResponseSchema:
    """Validate user credentials using request body and issue auth tokens."""
    return await _authenticate_and_issue_token(
        body.username, body.password, auth_service, user_service
    )


@router.post(
    "/oauth2-login",
    summary="OAuth2 scheme user login",
    description=(
        "Authenticate user based on OAuth2 login scheme "
        "and return a valid JWT auth tokens."
    ),
    response_model=LoginTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully authenticated user.",
    responses={**ON_LOGIN_USER_ERRORS_RESPONSES},
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> LoginTokenResponseSchema:
    """Validate user credentials using OAuth2 scheme and issue auth tokens."""
    return await _authenticate_and_issue_token(
        form_data.username, form_data.password, auth_service, user_service
    )


@router.post(
    "/refresh",
    summary="Issue access token based on valid refresh token",
    response_model=AccessTokenResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successfully issued a new access token.",
)
async def issue_access_token_on_refresh_token(
    body: RefreshTokenRequestSchema,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> AccessTokenResponseSchema:
    """Issue access token based on refresh token."""
    try:
        refresh_token_data = auth_service.decode_refresh_token(
            body.refresh_token.get_secret_value(),
        )
    except InvalidTokenError:
        raise_http_401_error(MESSAGE_ERROR_INVALID_OR_EXPIRED_REFRESH_TOKEN)

    user_id = int(refresh_token_data["sub"])
    token_id = refresh_token_data["jti"]

    user = await user_service.get_user_by_id(user_id)
    if not user:
        logger.warning(
            "Failed to validate refresh token (jti=%s): User with id=%s does not exists",
            token_id,
            user_id,
        )
        raise_http_401_error(MESSAGE_ERROR_INVALID_OR_EXPIRED_REFRESH_TOKEN)

    is_active_user = user.is_active
    if not is_active_user:
        logger.warning(
            "Refresh token (jti=%s) used by inactive user_id=%s",
            token_id,
            user_id,
        )
        raise_http_401_error(MESSAGE_ERROR_INVALID_OR_EXPIRED_REFRESH_TOKEN)

    access_token = auth_service.create_access_token(user_id)

    logger.info(
        "Refresh token jti=%s validated successfully for %s user with user_id=%s",
        token_id,
        "active" if is_active_user else "deactivated",
        user_id,
    )

    return AccessTokenResponseSchema(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/verify-email/",
    summary="Verify user email using email verification token",
    status_code=(
        status.HTTP_302_FOUND
        if app_config.EMAIL_VERIFICATION_REDIRECT_URL
        else status.HTTP_200_OK
    ),
    responses={
        **(
            ON_VERIFIED_EMAIL_SUCCESS_RESPONSE_WITH_REDIRECT
            if app_config.EMAIL_VERIFICATION_REDIRECT_URL
            else ON_VERIFIED_EMAIL_SUCCESS_RESPONSE
        ),
        **ON_VERIFY_EMAIL_BAD_REQUEST_RESPONSE,
    },
)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    """Confirm user email based on email verification token."""
    # Decode token to get username and email
    try:
        token_data = auth_service.decode_email_verification_token(token)
    except InvalidTokenError as exc:
        logger.debug("Can't verify user email: %s", str(exc))
        raise_http_400_error(MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN)

    user_id = int(token_data["sub"])
    email = token_data["email"]

    # Confirm user email
    try:
        user: UserDTO = await user_service.confirm_user_email(user_id, email)
    except InvalidUserCredentialsError as exc:
        logger.debug(
            "Can't verify user email for user_id=%s and email=%s: %s",
            user_id,
            email,
            str(exc),
        )
        raise_http_400_error(MESSAGE_ERROR_INVALID_OR_EXPIRED_MAIL_TOKEN)
    except UserInactiveError as exc:
        logger.debug(
            "%s for user_id=%s and email=%s",
            str(exc),
            user_id,
            email,
        )
        raise_http_403_error("Verification of email for inactive user is not allowed")
    except UserEmailIsAlreadyConfirmedError as exc:
        logger.debug(
            "Can't verify previously verified email for user_id=%s and email=%s: %s",
            user_id,
            email,
            str(exc),
        )
        raise_http_400_error(MESSAGE_ERROR_USER_EMAIL_IS_ALREADY_VERIFIED)

    logger.info("Email verified for %s", user)

    redirect_url = app_config.EMAIL_VERIFICATION_REDIRECT_URL
    if redirect_url:
        return RedirectResponse(url=redirect_url, status_code=HTTP_302_FOUND)

    return {"detail": MESSAGE_SUCCESS_EMAIL_VERIFIED}


async def _authenticate_and_issue_token(
    username: str,
    password: str,
    auth_service: AuthService,
    user_service: UserService,
) -> LoginTokenResponseSchema:
    """Process user credentials and issue access token"""
    # Check user credentials
    try:
        user: UserDTO = await user_service.validate_user_credentials(username, password)
    except InvalidUserCredentialsError as exc:
        logger.warning(
            "Failed login attempt: Not valid credentials for username '%s': %s",
            username,
            str(exc),
        )
        raise_http_401_error(MESSAGE_ERROR_INVALID_LOGIN_CREDENTIALS)

    # Check if user email is confirmed (except for superadmin)
    if not user.is_email_confirmed and user.role != UserRole.SUPERADMIN:
        logger.debug(
            "Failed login attempt: Email not verified for username '%s' (user_id=%s).",
            username,
            user.id,
        )
        raise_http_401_error(MESSAGE_ERROR_EMAIL_VERIFICATION_REQUIRED)

    # Generate access and refresh tokens
    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    logger.debug(
        (
            "User(id=%s, username=%s, role=%s, is_active=%s) "
            "authenticated successfully, issued with access and refresh tokens."
        ),
        user.id,
        user.username,
        user.role,
        user.is_active,
    )

    return LoginTokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )
