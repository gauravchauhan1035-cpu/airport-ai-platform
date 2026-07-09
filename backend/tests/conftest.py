"""Pytest configuration and shared fixtures."""

import os

# Use in-memory SQLite for unit tests unless overridden by fixture
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("LOG_PATH", "./data/logs")
