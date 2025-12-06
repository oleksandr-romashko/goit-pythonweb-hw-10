"""
CORS (Cross-Origin Resource Sharing) middleware configuration.

This module initializes CORS support for the FastAPI application.
It allows controlled access to the API from specified frontend origins.

Typical usage:
    from src.api.extensions.cors import init_cors
    init_cors(app)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import app_config
from src.utils.logger import logger


def init_cors(app: FastAPI) -> None:
    """
    Initialize CORS middleware for the FastAPI app.

    Reads allowed origins from configuration and applies appropriate
    access-control headers to HTTP responses.

    Notes:
        - Avoid using '*' (wildcard) in production, as it allows any origin.
        - If no origins are specified, CORS middleware is skipped entirely.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    origins = app_config.CORS_ORIGINS

    if not origins and app_config.DEV_ENV:
        logger.warning("No CORS_ORIGINS specified, using '*' for DEV mode.")
        origins = ["*"]

    if not origins:
        logger.warning(
            "CORS is not configured — no origins specified. "
            "Frontend apps will be unable to access the API from browsers."
        )
        return

    if "*" in origins:
        logger.warning(
            "CORS wildcard ('*') is enabled. "
            "This should only be used in development mode "
            "(currently development mode is %s).",
            "ON" if app_config.DEV_ENV else "OFF",
        )

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,  # allow cross-domain req incl. credentials (cookies, auth headers)
        allow_origins=["*"] if app_config.DEV_ENV else origins,  # allowed sources
        allow_methods=(
            ["*"]
            if app_config.DEV_ENV
            else ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        ),
        allow_headers=(
            ["*"]
            if app_config.DEV_ENV
            else [
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "Location",
                "X-Requested-With",
                "X-Process-Time",
            ]
        ),
    )

    logger.info("CORS middleware initialized for origins: %s", ", ".join(origins))
