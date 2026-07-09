"""Database health utilities."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database_connection(db: Session) -> bool:
    """Verify database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
