"""Pagination Pydantic schema."""

from typing import List, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationFilterRequestSchema(BaseModel):
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


class PaginatedGenericResponseSchema(
    PaginationFilterRequestSchema, BaseModel, Generic[T]
):
    """Schema for response with pagination"""

    total: int = Field(
        description="Total number of items available.",
        ge=0,
        json_schema_extra={"example": 1},
    )
    data: List[T]
