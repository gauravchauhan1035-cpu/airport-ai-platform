"""001 initial schema – operational_metrics and users tables.

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Operational metrics table
    op.create_table(
        "operational_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("zone_code", sa.String(length=20), nullable=False),
        sa.Column("zone_name", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metrics_zone_name", "operational_metrics", ["zone_code", "metric_name"])
    op.create_index("ix_metrics_recorded_at", "operational_metrics", ["recorded_at"])
    op.create_index(op.f("ix_operational_metrics_metric_name"), "operational_metrics", ["metric_name"])
    op.create_index(op.f("ix_operational_metrics_zone_code"), "operational_metrics", ["zone_code"])


def downgrade() -> None:
    op.drop_table("operational_metrics")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
