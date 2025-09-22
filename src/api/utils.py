"""Utility API endpoints for the application."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db
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
async def check_app_health(db: AsyncSession = Depends(get_db)):
    """Check if the API and database are up and running."""
    try:
        result = await db.execute(text("SELECT 1"))
        scalar: Optional[int] = result.scalar_one_or_none()

        if scalar is None:
            logger.error("Database is not configured correctly")
            raise_http_500_error("Database is not configured correctly")
        logger.info("Health check OK")
        return {"status": "ok"}
    except SQLAlchemyError:
        logger.error("Error connecting to the database", exc_info=True)
        raise_http_500_error("Error connecting to the database")
