"""
Main entry point for the FastAPI application.

Initializes the FastAPI app, registers all routers, and configures
global exception handlers. If run directly, starts a Uvicorn server.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
import uvicorn

from src.api.errors.handlers import init_exception_handlers
from src.api.extensions import (
    add_processing_time_header,
    close_rate_limiter,
    init_cors,
    init_rate_limiter,
    init_user_context,
)
from src.api.extensions.rate_limiter import get_rate_limit, RateLimit
from src.api.routers import (
    auth_router,
    contacts_router,
    me_router,
    root_router,
    users_router,
    utils_router,
)
from src.config import app_config
from src.utils.logger import logger


# TODO: Create possibility to invalidate access tokens (e.g. on password change)
# TODO: Add superadmin app management endpoints to disable registration, sending emails, serving web, cache, etc.
# TODO: Add feature - blacklist (cached)
# TODO: Add feature - whitelist set in .env for trusted resources omitting additional checks
# TODO: Clean up User account that was not confirmed (email confirmation) within X hours/days


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncIterator[None]:  # pylint: disable=unused-argument
    """
    Application lifespan context manager.

    Runs once on startup and shutdown.
    Resource initialization or cleanup tasks are located here
    (e.g., start/stop logging, cache and other connections).
    """
    logger.info("Application startup initiated")
    await init_rate_limiter()
    yield
    await close_rate_limiter()
    logger.info("Application shutdown complete")


app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(get_rate_limit(RateLimit.GLOBAL))],
    title=app_config.APP_TITLE,
    version=app_config.APP_VERSION,
    description=app_config.APP_DESCRIPTION,
    contact=app_config.APP_CONTACT,
    license_info=app_config.APP_LICENSE_INFO,
    # https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
    swagger_ui_parameters={
        "persistAuthorization": False,
        "tryItOutEnabled": False,
        "displayRequestDuration": True,
        "syntaxHighlight": {"theme": "agate"},
        "docExpansion": "list",
        "defaultModelsExpandDepth": -1,  # Hides schemas section completely
    },
)

# CORS middleware
init_cors(app)

# User context middleware
init_user_context(app)

# Processing time header middleware
if app_config.DEV_ENV:
    add_processing_time_header(app)

# Error handlers for common errors and consistent response
init_exception_handlers(app)

# Routes
app.include_router(root_router)
app.include_router(utils_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(me_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")

# Static files serving
app.mount("/static", StaticFiles(directory=app_config.STATIC_DIR), name="static")

if __name__ == "__main__":
    # Local run only (used by debugger)
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=app_config.WEB_PORT,
        reload=True,
        log_level="debug",
    )
