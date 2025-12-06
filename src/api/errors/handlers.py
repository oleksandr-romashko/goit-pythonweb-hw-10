"""Module for adding error handlers to the app"""

import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import app_config
from src.utils.constants import MESSAGE_ERROR_INTERNAL_SERVER_ERROR
from src.utils.logger import logger


def init_exception_handlers(app: FastAPI) -> None:
    """Initializes app with error handlers"""

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
        """
        Handle all Starlette and FastAPI HTTPExceptions.

        Logs error and return unify response.
        """
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
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_global_exception(
        request: Request, exc: Exception  # pylint: disable=unused-argument
    ) -> JSONResponse:
        """
        Catch all unhandled exceptions.

        Logs error and return unify sanitized response.
        """
        logger.exception("Unhandled exception: %s", exc)
        if app_config.DEV_ENV:
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
