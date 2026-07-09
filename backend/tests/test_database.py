"""Tests for database initialization and repository."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.init_db import SEED_METRICS, get_schema_description, seed_if_empty
from app.models import OperationalMetric, User
from app.repositories.metrics_repository import MetricsRepository


@pytest.fixture()
def test_db(tmp_path: Path) -> Session:
    """Create an isolated SQLite database for each test."""
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    db = TestSession()
    seed_if_empty(db)
    yield db
    db.close()
    test_engine.dispose()


def test_database_initialization_creates_tables(test_db: Session) -> None:
    assert test_db.query(OperationalMetric).count() == len(SEED_METRICS)
    assert test_db.query(User).count() == 3


def test_seed_is_idempotent(test_db: Session) -> None:
    initial_count = test_db.query(OperationalMetric).count()
    seed_if_empty(test_db)
    assert test_db.query(OperationalMetric).count() == initial_count


def test_metrics_repository_count(test_db: Session) -> None:
    repo = MetricsRepository(test_db)
    assert repo.count_all() == len(SEED_METRICS)


def test_metrics_repository_distinct_zones(test_db: Session) -> None:
    repo = MetricsRepository(test_db)
    zones = repo.get_distinct_zones()
    assert "CNS" in zones
    assert "T1" in zones
    assert len(zones) >= 5


def test_metrics_repository_average_temperature_cns(test_db: Session) -> None:
    repo = MetricsRepository(test_db)
    avg = repo.get_average_by_zone_and_metric("CNS", "temperature")
    assert avg is not None
    assert 20.0 < avg < 25.0


def test_metrics_repository_pagination(test_db: Session) -> None:
    repo = MetricsRepository(test_db)
    items, total = repo.list_paginated(page=1, page_size=5)
    assert len(items) == 5
    assert total == len(SEED_METRICS)


def test_metrics_repository_filter_by_zone(test_db: Session) -> None:
    repo = MetricsRepository(test_db)
    items, total = repo.list_paginated(zone_code="CNS")
    assert total > 0
    assert all(item.zone_code == "CNS" for item in items)


def test_schema_description_contains_table_info() -> None:
    schema = get_schema_description()
    assert "operational_metrics" in schema
    assert "zone_code" in schema
    assert "metric_name" in schema
