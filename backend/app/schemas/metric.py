"""Pydantic schemas for operational metrics."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricBase(BaseModel):
    """Shared metric fields."""

    zone_code: str
    zone_name: str
    metric_name: str
    metric_value: float
    unit: str


class MetricResponse(MetricBase):
    """Single metric record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    created_at: datetime


class MetricListResponse(BaseModel):
    """Paginated metrics list."""

    items: list[MetricResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MetricSummaryResponse(BaseModel):
    """Dashboard summary for metrics."""

    total_metrics: int
    zones: list[str]
    metric_types: list[str]


class MetricQueryParams(BaseModel):
    """Query parameters for metrics listing."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    zone_code: str | None = None
    metric_name: str | None = None
    search: str | None = None
    sort_by: str = "recorded_at"
    sort_order: str = "desc"
