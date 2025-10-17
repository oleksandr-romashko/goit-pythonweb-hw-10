"""Pydantic schemas for application utilities."""

from pydantic import BaseModel, Field


class HealthCheckResponseSchema(BaseModel):
    """Schema for application health check in responses."""

    status: str = Field(json_schema_extra={"example": "ok"})
