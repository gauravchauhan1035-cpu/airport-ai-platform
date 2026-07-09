"""Dashboard analytics API – KPIs, zone summaries, recent activity, and trends."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.operational_metric import OperationalMetric
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _avg_metric(db: Session, metric_name: str, zone_code: str | None = None) -> float | None:
    """Helper: compute average value for a given metric (optionally filtered by zone)."""
    q = db.query(func.avg(OperationalMetric.metric_value)).filter(
        OperationalMetric.metric_name == metric_name
    )
    if zone_code:
        q = q.filter(OperationalMetric.zone_code == zone_code)
    result = q.scalar()
    return round(float(result), 2) if result is not None else None


@router.get("/kpis")
def get_kpis(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Return high-level airport KPIs aggregated across all zones."""
    logger.info("Fetching dashboard KPIs")

    total_metrics = db.query(func.count(OperationalMetric.id)).scalar() or 0
    total_zones = db.query(func.count(func.distinct(OperationalMetric.zone_code))).scalar() or 0

    return {
        "total_metrics": total_metrics,
        "total_zones": total_zones,
        "avg_temperature": _avg_metric(db, "temperature"),
        "avg_security_wait_minutes": _avg_metric(db, "security_wait_time"),
        "flights_per_hour": _avg_metric(db, "flights_per_hour"),
        "runway_occupancy_pct": _avg_metric(db, "runway_occupancy"),
        "baggage_throughput": _avg_metric(db, "throughput"),
        "system_uptime_pct": _avg_metric(db, "system_uptime"),
        "active_flights": _avg_metric(db, "active_flights"),
        "avg_humidity": _avg_metric(db, "humidity"),
    }


@router.get("/zone-summary")
def get_zone_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Return per-zone average values for all metrics."""
    logger.info("Fetching zone summary")

    rows = (
        db.query(
            OperationalMetric.zone_code,
            OperationalMetric.zone_name,
            OperationalMetric.metric_name,
            func.avg(OperationalMetric.metric_value).label("avg_value"),
            OperationalMetric.unit,
        )
        .group_by(
            OperationalMetric.zone_code,
            OperationalMetric.zone_name,
            OperationalMetric.metric_name,
            OperationalMetric.unit,
        )
        .order_by(OperationalMetric.zone_code, OperationalMetric.metric_name)
        .all()
    )

    # Group by zone
    zones: dict[str, dict] = {}
    for row in rows:
        key = row.zone_code
        if key not in zones:
            zones[key] = {
                "zone_code": row.zone_code,
                "zone_name": row.zone_name,
                "metrics": {},
            }
        zones[key]["metrics"][row.metric_name] = {
            "avg": round(float(row.avg_value), 2),
            "unit": row.unit,
        }

    return list(zones.values())


@router.get("/recent-activity")
def get_recent_activity(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Return the most recently recorded metric entries."""
    logger.info("Fetching recent activity (limit=%d)", limit)

    items = (
        db.query(OperationalMetric)
        .order_by(OperationalMetric.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": item.id,
            "zone_code": item.zone_code,
            "zone_name": item.zone_name,
            "metric_name": item.metric_name,
            "metric_value": item.metric_value,
            "unit": item.unit,
            "recorded_at": item.recorded_at.isoformat() if item.recorded_at else None,
        }
        for item in items
    ]


@router.get("/trends")
def get_trends(
    metric_name: str = "temperature",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    """Return per-zone averages for a metric, grouped as trend data points.

    Since seeded data doesn't have time variance, we return zone-level averages
    as trend buckets suitable for charting.
    """
    logger.info("Fetching trends for metric=%s", metric_name)

    rows = (
        db.query(
            OperationalMetric.zone_code,
            OperationalMetric.zone_name,
            func.avg(OperationalMetric.metric_value).label("avg_value"),
            OperationalMetric.unit,
        )
        .filter(OperationalMetric.metric_name == metric_name)
        .group_by(
            OperationalMetric.zone_code,
            OperationalMetric.zone_name,
            OperationalMetric.unit,
        )
        .all()
    )

    return [
        {
            "zone_code": row.zone_code,
            "zone_name": row.zone_name,
            "metric_name": metric_name,
            "avg_value": round(float(row.avg_value), 2),
            "unit": row.unit,
        }
        for row in rows
    ]
