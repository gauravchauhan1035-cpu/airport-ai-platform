"""Health check endpoints."""

import os

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.health import check_database_connection
from app.database.session import get_db
from app.repositories.metrics_repository import MetricsRepository

router = APIRouter()


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Basic liveness check for Docker and load balancers."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/health/ready")
async def readiness_check(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> dict:
    """Readiness check including downstream Ollama and database connectivity."""
    db_status = "healthy" if check_database_connection(db) else "unhealthy"

    ollama_status = "unknown"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except httpx.HTTPError:
        ollama_status = "unreachable"

    # Check FAISS index by verifying the index file exists on disk
    faiss_path = "/app/data/faiss/index.faiss"
    faiss_status = "configured" if os.path.exists(faiss_path) else "not initialized"

    # Count metrics rows
    repo = MetricsRepository(db)
    metrics_count = repo.count_all()

    overall = "ready" if db_status == "healthy" and ollama_status == "healthy" else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "ollama": ollama_status,
        "faiss": faiss_status,
        "metrics_count": metrics_count,
    }
