"""User context middleware configuration"""

from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.security import jwt_utils
from src.config import app_config


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    User context middleware to add user_id context to the request state
    whether Authorization token is not valid anyway provided.

    Token will be decoded and user_id extracted if the token has a valid signature.
    Signature is always validated (not allowed to bypass it unless explicitly configured).
    The following verifications won't take place:
    - if token is expired (EXP claim)
    - if token validity starts in the future (NBF claim)
    - if token has wrong audience (AUD claim)
    - if token has wrong type (custom token_type claim)
    This is intentional: rate limiter identifies by user_id when possible.
    Full JWT validation happens later in dependencies.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.user_id = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt_utils.decode_token(
                    token,
                    secret_key=app_config.AUTH_JWT_SECRET,
                    algorithms=[app_config.AUTH_JWT_ALGORITHM],
                    verify_exp=False,
                    verify_nbf=False,
                    expected_audience=None,
                    expected_token_type=None,
                )
                request.state.user_id = payload.get("sub")
            except (jwt_utils.ExpiredTokenError, jwt_utils.MalformedTokenError):
                # Just skip adding user_id and continue processing th request
                pass

        return await call_next(request)


def init_user_context(app: FastAPI) -> None:
    """
    Initialize adding user context by adding user_id
    to the request state whether Authorization token is provided.
    """
    app.add_middleware(UserContextMiddleware)  # type: ignore
