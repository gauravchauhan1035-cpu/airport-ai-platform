"""Tests for the Metrics API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.init_db import seed_if_empty
from app.database.session import get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    """Test client wired to an isolated database with seeded data and admin auth."""
    db_url = f"sqlite:///{tmp_path}/test_metrics_api.db"
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
        # Log in as admin to get a token for protected endpoints
        login = c.post("/login", json={"username": "admin", "password": "Admin123!"})
        token = login.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def test_metrics_summary(client):
    response = client.get("/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_metrics" in data
    assert data["total_metrics"] > 0
    assert "zones" in data
    assert len(data["zones"]) >= 5
    assert "metric_types" in data


def test_metrics_list_default(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1
    assert len(data["items"]) > 0


def test_metrics_list_pagination(client):
    response = client.get("/metrics?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page_size"] == 5


def test_metrics_list_filter_by_zone(client):
    response = client.get("/metrics?zone_code=T1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["zone_code"] == "T1"


def test_metrics_list_filter_by_metric_name(client):
    response = client.get("/metrics?metric_name=temperature")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert item["metric_name"] == "temperature"


def test_metrics_list_search(client):
    response = client.get("/metrics?search=Terminal")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0


def test_metrics_list_invalid_sort(client):
    response = client.get("/metrics?sort_by=nonexistent_col")
    assert response.status_code == 400


def test_metrics_zones(client):
    response = client.get("/metrics/zones")
    assert response.status_code == 200
    zones = response.json()
    assert isinstance(zones, list)
    assert "CNS" in zones
    assert "RWY" in zones


def test_metrics_get_by_id(client):
    # Get first metric ID from list
    list_resp = client.get("/metrics?page_size=1")
    first_id = list_resp.json()["items"][0]["id"]

    response = client.get(f"/metrics/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_id


def test_metrics_get_by_id_not_found(client):
    response = client.get("/metrics/999999")
    assert response.status_code == 404
