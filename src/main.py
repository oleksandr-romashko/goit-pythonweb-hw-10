"""
Main entry point for the FastAPI application.

Initializes the FastAPI app, registers all routers, and configures
global exception handlers. If run directly, starts a Uvicorn server.
"""

import traceback
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


from src.api.routers import (
    auth_router,
    contacts_router,
    me_router,
    root_router,
    users_router,
    utils_router,
)
from src.config import app_config
from src.utils.constants import MESSAGE_ERROR_INTERNAL_SERVER_ERROR
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncIterator[None]:  # pylint: disable=unused-argument
    """
    Application lifespan context manager.

    Runs once on startup and shutdown. Place resource initialization
    or cleanup tasks here (e.g., database connections).
    """
    logger.info("Application startup initiated")
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    lifespan=lifespan,
    title=app_config.APP_TITLE,
    version=app_config.APP_VERSION,
    description=app_config.APP_DESCRIPTION,
    contact={
        "name": app_config.APP_AUTHOR_NAME,
        "url": app_config.APP_HOMEPAGE,
        "email": app_config.APP_AUTHOR_EMAIL,
    },
    license_info={
        "name": f"{app_config.APP_LICENSE_TITLE} License",
        "url": app_config.APP_LICENSE_URL,
    },
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


app.include_router(root_router)
app.include_router(utils_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(me_router, prefix="/api")
app.include_router(contacts_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic/body/query validation failures (HTTP 422).

    Logs the validation error and then delegates to FastAPI's
    default `request_validation_exception_handler` so the
    response shape and OpenAPI schema remain unchanged.
    """
    logger.warning(
        "Validation error on %s %s: %s",
        request.method,
        request.url,
        exc.errors(),
    )
    # Delegate to FastAPI's default implementation
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle all Starlette and FastAPI HTTPExceptions and unify response."""
    logger.info(
        "HTTP %s: %s %s%s",
        exc.status_code,
        request.method,
        request.url.path,
        f"?{request.url.query}" if request.url.query else "",
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def handle_global_exception(
    request: Request, exc: Exception  # pylint: disable=unused-argument
) -> JSONResponse:
    """Catch all unhandled exceptions."""
    logger.exception("Unhandled exception: %s", exc)
    if app_config.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"Unhandled exceptions caused {MESSAGE_ERROR_INTERNAL_SERVER_ERROR}",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": MESSAGE_ERROR_INTERNAL_SERVER_ERROR},
    )


def main() -> None:
    """Run Uvicorn server for development."""
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=app_config.WEB_PORT,
        reload=app_config.DEBUG,
    )


if __name__ == "__main__":
    main()
