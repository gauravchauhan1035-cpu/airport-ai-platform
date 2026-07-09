"""Tests for authentication: login, token validation, protected routes, and RBAC."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.auth.jwt import create_access_token, decode_access_token
from app.auth.password import hash_password, verify_password
from app.database.base import Base
from app.database.init_db import seed_if_empty
from app.database.session import get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    """Test client wired to an isolated database with seeded users."""
    db_url = f"sqlite:///{tmp_path}/test_auth.db"
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
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


# ── Password Utilities ────────────────────────────────────────────────────────

def test_hash_and_verify_password():
    plain = "SuperSecret99!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("WrongPassword", hashed)


# ── JWT Utilities ─────────────────────────────────────────────────────────────

def test_create_and_decode_token():
    token = create_access_token({"sub": "testuser", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"


def test_decode_invalid_token():
    result = decode_access_token("not.a.valid.token")
    assert result is None


# ── Login Endpoint ─────────────────────────────────────────────────────────────

def test_login_success_admin(client):
    response = client.post("/login", json={"username": "admin", "password": "Admin123!"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_success_analyst(client):
    response = client.post("/login", json={"username": "analyst", "password": "Analyst123!"})
    assert response.status_code == 200


def test_login_success_viewer(client):
    response = client.post("/login", json={"username": "viewer", "password": "Viewer123!"})
    assert response.status_code == 200


def test_login_wrong_password(client):
    response = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post("/login", json={"username": "ghost", "password": "anything"})
    assert response.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

def test_get_me_authenticated(client):
    login = client.post("/login", json={"username": "admin", "password": "Admin123!"})
    token = login.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_get_me_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


# ── Protected Metrics Endpoints ───────────────────────────────────────────────

def test_metrics_requires_auth(client):
    response = client.get("/metrics")
    assert response.status_code == 401


def test_metrics_accessible_with_token(client):
    login = client.post("/login", json={"username": "viewer", "password": "Viewer123!"})
    token = login.json()["access_token"]
    response = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


# ── Logout ────────────────────────────────────────────────────────────────────

def test_logout_success(client):
    login = client.post("/login", json={"username": "admin", "password": "Admin123!"})
    token = login.json()["access_token"]
    response = client.post("/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204


def test_logout_unauthenticated(client):
    response = client.post("/logout")
    assert response.status_code == 401
