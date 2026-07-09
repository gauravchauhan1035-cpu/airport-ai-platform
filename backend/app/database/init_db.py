"""Database initialization and seeding."""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import Settings
from app.database.base import Base
from app.database.session import engine
from app.models import OperationalMetric, User
from app.models.user import UserRole

logger = logging.getLogger(__name__)

# Seed data: realistic airport operational metrics across zones
SEED_METRICS: list[dict] = [
    # CNS - Central Navigation System
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "temperature", "metric_value": 22.5, "unit": "C"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "temperature", "metric_value": 23.1, "unit": "C"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "temperature", "metric_value": 21.8, "unit": "C"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "humidity", "metric_value": 45.0, "unit": "%"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "humidity", "metric_value": 48.2, "unit": "%"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "air_quality_index", "metric_value": 32.0, "unit": "AQI"},
    {"zone_code": "CNS", "zone_name": "Central Navigation System", "metric_name": "system_uptime", "metric_value": 99.7, "unit": "%"},
    # T1 - Terminal 1
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "temperature", "metric_value": 24.0, "unit": "C"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "temperature", "metric_value": 24.5, "unit": "C"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "passenger_count", "metric_value": 1250.0, "unit": "count"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "passenger_count", "metric_value": 980.0, "unit": "count"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "security_wait_time", "metric_value": 12.5, "unit": "minutes"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "security_wait_time", "metric_value": 8.3, "unit": "minutes"},
    {"zone_code": "T1", "zone_name": "Terminal 1", "metric_name": "humidity", "metric_value": 52.0, "unit": "%"},
    # T2 - Terminal 2
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "temperature", "metric_value": 23.2, "unit": "C"},
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "temperature", "metric_value": 22.9, "unit": "C"},
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "passenger_count", "metric_value": 870.0, "unit": "count"},
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "passenger_count", "metric_value": 1100.0, "unit": "count"},
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "security_wait_time", "metric_value": 15.0, "unit": "minutes"},
    {"zone_code": "T2", "zone_name": "Terminal 2", "metric_name": "gate_utilization", "metric_value": 78.5, "unit": "%"},
    # RUNWAY
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "temperature", "metric_value": 18.5, "unit": "C"},
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "wind_speed", "metric_value": 14.2, "unit": "knots"},
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "wind_speed", "metric_value": 11.8, "unit": "knots"},
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "visibility", "metric_value": 10.0, "unit": "km"},
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "runway_occupancy", "metric_value": 65.0, "unit": "%"},
    {"zone_code": "RWY", "zone_name": "Runway Operations", "metric_name": "flights_per_hour", "metric_value": 42.0, "unit": "count"},
    # BHS - Baggage Handling System
    {"zone_code": "BHS", "zone_name": "Baggage Handling System", "metric_name": "throughput", "metric_value": 320.0, "unit": "bags/hour"},
    {"zone_code": "BHS", "zone_name": "Baggage Handling System", "metric_name": "throughput", "metric_value": 285.0, "unit": "bags/hour"},
    {"zone_code": "BHS", "zone_name": "Baggage Handling System", "metric_name": "error_rate", "metric_value": 0.3, "unit": "%"},
    {"zone_code": "BHS", "zone_name": "Baggage Handling System", "metric_name": "temperature", "metric_value": 20.1, "unit": "C"},
    {"zone_code": "BHS", "zone_name": "Baggage Handling System", "metric_name": "conveyor_speed", "metric_value": 1.8, "unit": "m/s"},
    # ATC - Air Traffic Control
    {"zone_code": "ATC", "zone_name": "Air Traffic Control", "metric_name": "active_flights", "metric_value": 28.0, "unit": "count"},
    {"zone_code": "ATC", "zone_name": "Air Traffic Control", "metric_name": "active_flights", "metric_value": 35.0, "unit": "count"},
    {"zone_code": "ATC", "zone_name": "Air Traffic Control", "metric_name": "delay_minutes_avg", "metric_value": 6.5, "unit": "minutes"},
    {"zone_code": "ATC", "zone_name": "Air Traffic Control", "metric_name": "system_uptime", "metric_value": 99.99, "unit": "%"},
]


def ensure_database_directory(settings: Settings) -> None:
    """Create SQLite directory if using a file-based database."""
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def init_database(settings: Settings) -> None:
    """Create all tables and seed initial data if empty."""
    ensure_database_directory(settings)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


def seed_if_empty(db: Session) -> None:
    """Seed operational metrics and default users when tables are empty."""
    metric_count = db.query(OperationalMetric).count()
    if metric_count == 0:
        logger.info("Seeding operational metrics...")
        for entry in SEED_METRICS:
            db.add(OperationalMetric(**entry))
        db.commit()
        logger.info("Seeded %d operational metrics", len(SEED_METRICS))
    else:
        logger.info("Operational metrics already seeded (%d rows)", metric_count)

    user_count = db.query(User).count()
    if user_count == 0:
        logger.info("Seeding default users with bcrypt-hashed passwords (MUST CHANGE ON FIRST LOGIN)...")
        from app.auth.password import hash_password

        # Security: Default passwords should be changed immediately in production
        default_users = [
            User(
                username="admin",
                hashed_password=hash_password("Admin!2026#ChangeMeNow"),
                role=UserRole.ADMIN.value,
            ),
            User(
                username="analyst",
                hashed_password=hash_password("Analyst!2026#ChangeMeNow"),
                role=UserRole.ANALYST.value,
            ),
            User(
                username="viewer",
                hashed_password=hash_password("Viewer!2026#ChangeMeNow"),
                role=UserRole.VIEWER.value,
            ),
        ]
        db.add_all(default_users)
        db.commit()
        logger.info("Seeded %d default users", len(default_users))


def get_schema_description() -> str:
    """Return human-readable schema for SQL agent prompts.
    SECURITY: Internal columns (id, created_at, recorded_at) are intentionally omitted.
    """
    return """
Table: operational_metrics
Available Data:
  - zone_code (VARCHAR) — airport zone code, e.g. CNS, T1, T2, RWY, BHS, ATC
  - zone_name (VARCHAR) — full zone name
  - metric_name (VARCHAR) — e.g. temperature, humidity, passenger_count, security_wait_time
  - metric_value (FLOAT) — numeric reading
  - unit (VARCHAR) — e.g. C, %, count, minutes, knots, km

Example zones: CNS (Central Navigation System), T1, T2, RWY, BHS, ATC
Example metrics: temperature, humidity, passenger_count, security_wait_time, wind_speed
""".strip()
