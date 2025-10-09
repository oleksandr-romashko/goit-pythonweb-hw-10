"""Utility API endpoints for the application."""

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db_session
from src.schemas.errors import InternalServerErrorResponse
from src.schemas.utils import HealthCheckResponse
from src.utils.errors import raise_http_500_error
from src.utils.logger import logger

router = APIRouter(tags=["Utils"])


@router.get(
    "/healthchecker",
    response_model=HealthCheckResponse,
    summary="Check application health",
    description=(
        "Check if the API and database are up and running.\n\n"
        "Returns **'ok'** status if the database connection succeeds."
    ),
    responses={
        500: {
            "model": InternalServerErrorResponse,
            "description": (
                "Database is not configured correctly "
                "or error connecting to the database"
            ),
        },
    },
)
async def check_app_health(
    db_session: AsyncSession = Depends(get_db_session),
) -> HealthCheckResponse:
    """Check if the API and database are up and running, else raise 500."""
    await _ensure_db_connection(db_session)
    logger.info("Health check OK")
    return HealthCheckResponse.model_validate({"status": "ok"})


async def _ensure_db_connection(db_session: AsyncSession) -> None:
    """Try a simple DB query. Raise 500 if it fails."""
    try:
        result = await db_session.execute(text("SELECT 1"))
        if result.scalar_one_or_none() is None:
            logger.error("Database is not configured correctly")
            raise_http_500_error("Database is not configured correctly")
    except SQLAlchemyError:
        logger.error("Error connecting to the database", exc_info=True)
        raise_http_500_error("Error connecting to the database")
