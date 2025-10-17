"""FastAPI token dependencies"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.services.auth_service import AuthService
from src.services.errors import InvalidAccessTokenError
from src.utils.constants import MESSAGE_ERROR_INVALID_AUTH_TOKEN
from src.utils.logger import logger

from src.api.errors import raise_http_401_error

from .service_dependencies import get_auth_service


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/oauth2-login",
    scheme_name="🔒 Bearer token authentication",
    description=(
        "Authenticate using **OAuth2 password flow**.<br><br>"
        "Enter your ***username*** and ***password*** to obtain and store an access token.<br><br>"
        "**☝️ Please note:**<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "• Keep ***Client credentials location*** as 'Authorization header'."
        "<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "• Leave ***client_id*** and ***client_secret*** empty.<br><br>"
    ),
)


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    token_service: AuthService = Depends(get_auth_service),
) -> int:
    """Validate provided JWT token and extract user identifier from it."""
    # Decode token
    try:
        payload = token_service.decode_access_token(token)
    except InvalidAccessTokenError as exc:
        logger.warning(str(exc))
        raise_http_401_error(MESSAGE_ERROR_INVALID_AUTH_TOKEN)

    # Retrieve user identifier from the token subject claim
    user_id: int = int(payload["sub"])

    return user_id
