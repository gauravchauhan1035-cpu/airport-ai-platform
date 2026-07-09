"""Tests for dashboard analytics endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.init_db import seed_if_empty
from app.database.session import get_db
from app.main import app


@pytest.fixture()
def auth_client(tmp_path):
    """Test client with seeded DB and admin token pre-applied."""
    db_url = f"sqlite:///{tmp_path}/test_dashboard.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestSession()
    seed_if_empty(db)
    db.close()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        login = c.post("/login", json={"username": "admin", "password": "Admin123!"})
        token = login.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def test_dashboard_kpis(auth_client):
    response = auth_client.get("/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "total_metrics" in data
    assert data["total_metrics"] > 0
    assert "total_zones" in data
    assert data["total_zones"] >= 5
    assert "avg_temperature" in data


def test_dashboard_kpis_requires_auth(auth_client):
    # Use a raw client without the auth header
    from fastapi.testclient import TestClient as RawClient

    with RawClient(app) as raw:
        response = raw.get("/dashboard/kpis")
    assert response.status_code == 401


def test_dashboard_zone_summary(auth_client):
    response = auth_client.get("/dashboard/zone-summary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    for zone in data:
        assert "zone_code" in zone
        assert "metrics" in zone
        assert isinstance(zone["metrics"], dict)


def test_dashboard_recent_activity(auth_client):
    response = auth_client.get("/dashboard/recent-activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for item in data:
        assert "zone_code" in item
        assert "metric_name" in item
        assert "metric_value" in item


def test_dashboard_trends_temperature(auth_client):
    response = auth_client.get("/dashboard/trends?metric_name=temperature")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for point in data:
        assert point["metric_name"] == "temperature"
        assert "avg_value" in point
        assert "zone_code" in point
