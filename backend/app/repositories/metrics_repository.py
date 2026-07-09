"""Data access layer for operational metrics."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.operational_metric import OperationalMetric


class MetricsRepository:
    """Repository for querying operational metrics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def count_all(self) -> int:
        """Return total number of metric records."""
        return self.db.query(func.count(OperationalMetric.id)).scalar() or 0

    def get_distinct_zones(self) -> list[str]:
        """Return unique zone codes."""
        rows = (
            self.db.query(OperationalMetric.zone_code)
            .distinct()
            .order_by(OperationalMetric.zone_code)
            .all()
        )
        return [row[0] for row in rows]

    def get_distinct_metric_names(self) -> list[str]:
        """Return unique metric names."""
        rows = (
            self.db.query(OperationalMetric.metric_name)
            .distinct()
            .order_by(OperationalMetric.metric_name)
            .all()
        )
        return [row[0] for row in rows]

    def get_by_zone(self, zone_code: str, limit: int = 100) -> list[OperationalMetric]:
        """Return metrics for a specific zone."""
        return (
            self.db.query(OperationalMetric)
            .filter(OperationalMetric.zone_code == zone_code.upper())
            .order_by(OperationalMetric.recorded_at.desc())
            .limit(limit)
            .all()
        )

    def get_average_by_zone_and_metric(
        self, zone_code: str, metric_name: str
    ) -> float | None:
        """Return average metric value for zone and metric name."""
        result = (
            self.db.query(func.avg(OperationalMetric.metric_value))
            .filter(
                OperationalMetric.zone_code == zone_code.upper(),
                OperationalMetric.metric_name == metric_name.lower(),
            )
            .scalar()
        )
        return float(result) if result is not None else None

    def list_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        zone_code: str | None = None,
        metric_name: str | None = None,
        search: str | None = None,
        sort_by: str = "recorded_at",
        sort_order: str = "desc",
    ) -> tuple[list[OperationalMetric], int]:
        """Return paginated metrics with optional filters."""
        query = self.db.query(OperationalMetric)

        if zone_code:
            query = query.filter(OperationalMetric.zone_code == zone_code.upper())
        if metric_name:
            query = query.filter(OperationalMetric.metric_name == metric_name.lower())
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                (OperationalMetric.zone_code.ilike(pattern))
                | (OperationalMetric.zone_name.ilike(pattern))
                | (OperationalMetric.metric_name.ilike(pattern))
            )

        sort_column = getattr(OperationalMetric, sort_by, OperationalMetric.recorded_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
