"""Utility API endpoints for the application."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.utils.constants import (
    MESSAGE_ERROR_DB_CONNECTION_ERROR,
    MESSAGE_ERROR_DB_INVALID_CONFIG,
)
from src.utils.logger import logger

from src.api.dependencies import get_db_session
from src.api.errors import raise_http_500_error
from src.api.responses.error_responses import ON_INTERNAL_SERVER_ERROR_RESPONSE
from src.api.schemas.utils import HealthCheckResponseSchema

router = APIRouter(tags=["Utils (Public Access)"])


@router.get(
    "/healthchecker",
    summary="Check application health",
    description=(
        "Check if the API and database are up and running.\n\n"
        "Returns **'ok'** status if the database connection succeeds."
    ),
    response_model=HealthCheckResponseSchema,
    status_code=status.HTTP_200_OK,
    response_description="Successful health check.",
    responses={**ON_INTERNAL_SERVER_ERROR_RESPONSE},
)
async def check_app_health(
    db_session: AsyncSession = Depends(get_db_session),
) -> HealthCheckResponseSchema:
    """Check if the API and database are up and running, else raise 500."""
    await _ensure_db_connection(db_session)
    logger.info("Health check OK")
    return HealthCheckResponseSchema.model_validate({"status": "ok"})


async def _ensure_db_connection(db_session: AsyncSession) -> None:
    """Try a simple DB query. Raise 500 if it fails."""
    try:
        result = await db_session.execute(text("SELECT 1"))
        if result.scalar_one_or_none() is None:
            logger.error(
                "Database is not configured correctly. Received None on SELECT 1"
            )
            raise_http_500_error(MESSAGE_ERROR_DB_INVALID_CONFIG)
    except SQLAlchemyError:
        logger.error(
            (
                "Error connecting to the database. "
                "Wrong connection credentials, "
                "database is not running or responding or just can't reach it."
            ),
            exc_info=True,
        )
        raise_http_500_error(MESSAGE_ERROR_DB_CONNECTION_ERROR)
