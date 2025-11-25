"""
Root API endpoint.

Redirects to api documentation and serves static resources.
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, FileResponse

from src.config import app_config

router = APIRouter()


@router.get("/", include_in_schema=False)
async def get_root() -> RedirectResponse:
    """
    Root router handling

    Redirects to swagger documentation.
    """
    return RedirectResponse(url="/docs")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Serve the favicon.ico file."""
    return FileResponse(f"{app_config.STATIC_DIR}/images/favicon.ico")
