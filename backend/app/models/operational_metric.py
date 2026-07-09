"""Operational metrics stored in SQLite for SQL agent queries."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class OperationalMetric(Base):
    """Airport zone operational reading (temperature, wait times, etc.)."""

    __tablename__ = "operational_metrics"
    __table_args__ = (
        Index("ix_metrics_zone_name", "zone_code", "metric_name"),
        Index("ix_metrics_recorded_at", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    zone_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<OperationalMetric zone={self.zone_code} "
            f"metric={self.metric_name} value={self.metric_value}>"
        )
