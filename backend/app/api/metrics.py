"""Metrics API endpoints – paginated list, summary, zones, and single record."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.metrics_repository import MetricsRepository
from app.schemas.metric import MetricListResponse, MetricResponse, MetricSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary", response_model=MetricSummaryResponse)
def get_metrics_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MetricSummaryResponse:
    """Return aggregate summary: total count, zone list, metric type list."""
    repo = MetricsRepository(db)
    logger.info("Fetching metrics summary")
    return MetricSummaryResponse(
        total_metrics=repo.count_all(),
        zones=repo.get_distinct_zones(),
        metric_types=repo.get_distinct_metric_names(),
    )


@router.get("/zones", response_model=list[str])
def get_zones(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[str]:
    """Return all distinct zone codes."""
    repo = MetricsRepository(db)
    return repo.get_distinct_zones()


@router.get("", response_model=MetricListResponse)
def list_metrics(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    zone_code: str | None = Query(default=None, description="Filter by zone code"),
    metric_name: str | None = Query(default=None, description="Filter by metric name"),
    search: str | None = Query(default=None, description="Full-text search across zone/metric fields"),
    sort_by: str = Query(default="recorded_at", description="Column to sort by"),
    sort_order: str = Query(default="desc", description="asc or desc"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MetricListResponse:
    """Return paginated operational metrics with optional filters."""
    repo = MetricsRepository(db)

    valid_sort_cols = {"id", "zone_code", "zone_name", "metric_name", "metric_value", "recorded_at", "created_at"}
    if sort_by not in valid_sort_cols:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by column: {sort_by}")
    if sort_order.lower() not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")

    logger.info(
        "Listing metrics page=%d size=%d zone=%s metric=%s search=%s",
        page, page_size, zone_code, metric_name, search,
    )

    items, total = repo.list_paginated(
        page=page,
        page_size=page_size,
        zone_code=zone_code,
        metric_name=metric_name,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return MetricListResponse(
        items=[MetricResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{metric_id}", response_model=MetricResponse)
def get_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MetricResponse:
    """Return a single metric record by ID."""
    from app.models.operational_metric import OperationalMetric

    metric = db.query(OperationalMetric).filter(OperationalMetric.id == metric_id).first()
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    return MetricResponse.model_validate(metric)
