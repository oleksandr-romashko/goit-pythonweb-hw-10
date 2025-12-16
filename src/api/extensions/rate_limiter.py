"""
Application-wide request rate limiter.

Provides global and per-endpoint rate limiting.

Usage:
    ```
    @router.get(
        "/",
        ...
        dependencies=[Depends(RateLimiter(times=2, seconds=5))],
    )
    ```
"""

from math import ceil
from enum import Enum, auto
import sys
from typing import NoReturn

from fastapi import Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis.exceptions import ConnectionError as RedisConnectionError

from src.providers.cache_providers.connection import get_redis, RedisDB
from src.utils.constants import MESSAGE_ERROR_TOO_MANY_REQUESTS
from src.utils.logger import logger

# TODO: Apply all limits below to appropriate app routes
# ==========================
# Named rate limits for application-wide reuse
# ==========================


class RateLimit(Enum):
    """Defines available rate limit type."""

    GLOBAL = auto()
    AUTH = auto()
    AUTH_STRICT = auto()
    PASSWORD_RESET = auto()
    USER_CRUD = auto()
    ME = auto()
    CONTACTS_READ = auto()
    CONTACTS_WRITE = auto()
    UTILS = auto()


def get_rate_limit(rate_limit: RateLimit) -> RateLimiter:
    """Returns appropriate rate limiter based on limit type"""
    match rate_limit:
        # === 🌐 Global limit ===
        case RateLimit.GLOBAL:
            # app-wide
            return RateLimiter(times=1000, hours=1)
        # === 🔐 Auth & Security endpoints ===
        case RateLimit.AUTH:
            # for login/register/token
            return RateLimiter(times=5, minutes=1)
        case RateLimit.AUTH_STRICT:
            # for login/register/token
            # composite against sudden bursts and continuous flood.
            return RateLimiter(times=100, hours=1)
        case RateLimit.PASSWORD_RESET:
            return RateLimiter(times=100, hours=1)
        # === 👤 Users and user profile endpoints ===
        case RateLimit.USER_CRUD:
            # POST/PUT/DELETE on /users
            return RateLimiter(times=20, minutes=1)
        case RateLimit.ME:
            # /me
            return RateLimiter(times=10, minutes=1)
        # === 📇 Contacts-related endpoints ===
        case RateLimit.CONTACTS_READ:
            return RateLimiter(times=120, minutes=1)
        case RateLimit.CONTACTS_WRITE:
            return RateLimiter(times=30, minutes=1)
        # === ⚙️ Utility / public endpoints ===
        case RateLimit.UTILS:
            return RateLimiter(times=5000, hours=1)
        # === Other ===
        case _:
            raise ValueError("Unsupported rate limit type")


# ==========================
# Global limiter instance
# ==========================


async def default_identifier(request: Request):
    """Identifier of route limit, overriding default identifier of ip."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]

    method = request.method
    path = request.url.path

    # Extract user_id from request state
    if getattr(request.state, "user_id", None):
        user_id = request.state.user_id
        return f"user:{user_id}:{method}:{path}"

    # Fallback unauthenticated user by extracting IP
    base_id = request.client.host if request.client else "unknown"
    return f"ip:{base_id}:{method}:{path}"


async def exceed_limit_callback(
    request: Request, _response: Response, pexpire: int
) -> NoReturn:
    """
    Called when the request exceeds the rate limit.

    :param request: FastAPI request
    :param response: FastAPI response (ignored)
    :param pexpire: Remaining milliseconds until the limit resets
    """
    retry_after_seconds = ceil(pexpire / 1000)

    user_id = getattr(request.state, "user_id", None)
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    logger.warning(
        "Rate limit exceeded: %s %s | user_id=%s | ip=%s | user_agent=%s | retry_after=%s",
        request.method,
        request.url.path,
        user_id,
        ip,
        user_agent,
        retry_after_seconds,
    )
    raise HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        MESSAGE_ERROR_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(retry_after_seconds)},
    )


async def init_rate_limiter() -> None:
    """Initialize rate limiter"""
    logger.info("Initializing request rate limiter...")
    redis = get_redis(RedisDB.RATELIMIT)
    try:
        await FastAPILimiter.init(
            redis,
            identifier=default_identifier,
            http_callback=exceed_limit_callback,
            prefix="ratelimit",
        )
        logger.info("Request rate limiter initialization success.")
    except RedisConnectionError:
        logger.critical(
            (
                "✘ Failed to connect to Redis service with rate limiter. "
                "Please make sure username-password pair is valid or user is enabled. "
            ),
        )
        sys.exit(1)


async def close_rate_limiter() -> None:
    """Close rate rate limiter and free resources"""
    logger.info("Closings request rate limiter...")
    await FastAPILimiter.close()
    logger.info("Request rate limiter closed.")
