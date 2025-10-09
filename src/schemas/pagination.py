from pydantic import BaseModel, Field


class PaginationFilterSchema(BaseModel):
    """Schema for pagination queries."""

    skip: int = Field(
        default=0,
        description="Number of items to skip for pagination.",
        ge=0,
        json_schema_extra={"example": 0},
    )
    limit: int = Field(
        default=50,
        description="Maximum number of items to return.",
        ge=1,
        le=1000,
        json_schema_extra={"example": 50},
    )


async def get_pagination_filter(
    skip: int,
    limit: int,
) -> PaginationFilterSchema:
    """Dependency provider for pagination filter."""
    return PaginationFilterSchema(skip=skip, limit=limit)
