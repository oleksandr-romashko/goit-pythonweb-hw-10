"""
Root API endpoint.

Redirects to api documentation.
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/", include_in_schema=False)
async def get_root() -> RedirectResponse:
    """
    Root router handling

    Redirects to swagger documentation.
    """
    return RedirectResponse(url="/docs")
