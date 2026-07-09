"""Tests for the SQL agent's safety validation and extraction logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.sql_agent import SQLAgent, SQLAgentError
from app.database.base import Base
from app.database.init_db import seed_if_empty


@pytest.fixture()
def db_session(tmp_path):
    """Isolated in-memory DB with seeded data."""
    db_url = f"sqlite:///{tmp_path}/test_sql_agent.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    seed_if_empty(session)
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def agent(db_session):
    return SQLAgent(db_session)


# ── SQL Extraction ─────────────────────────────────────────────────────────────

def test_extract_plain_select(agent):
    sql = agent._extract_sql("SELECT * FROM operational_metrics LIMIT 5;")
    assert sql.upper().startswith("SELECT")


def test_extract_from_code_fence(agent):
    output = "```sql\nSELECT id FROM operational_metrics LIMIT 1;\n```"
    sql = agent._extract_sql(output)
    assert "SELECT" in sql.upper()


def test_extract_from_markdown_block(agent):
    output = "Here is your query:\n```\nSELECT zone_code FROM operational_metrics LIMIT 1;\n```"
    sql = agent._extract_sql(output)
    assert "SELECT" in sql.upper()


# ── SQL Validation ─────────────────────────────────────────────────────────────

def test_validate_select_passes(agent):
    agent._validate_sql("SELECT * FROM operational_metrics LIMIT 10")  # no exception


def test_validate_insert_raises(agent):
    with pytest.raises(SQLAgentError, match="Only SELECT"):
        agent._validate_sql("INSERT INTO users VALUES (1,'a','b','admin',1)")


def test_validate_update_raises(agent):
    with pytest.raises(SQLAgentError):
        agent._validate_sql("UPDATE operational_metrics SET metric_value = 0")


def test_validate_delete_raises(agent):
    with pytest.raises(SQLAgentError):
        agent._validate_sql("DELETE FROM operational_metrics")


def test_validate_drop_raises(agent):
    with pytest.raises(SQLAgentError):
        agent._validate_sql("DROP TABLE operational_metrics")


def test_validate_hidden_drop_raises(agent):
    with pytest.raises(SQLAgentError):
        agent._validate_sql("SELECT 1; DROP TABLE operational_metrics;")


# ── SQL Execution ──────────────────────────────────────────────────────────────

def test_execute_sql_returns_rows(agent):
    rows = agent._execute_sql(
        "SELECT zone_code, metric_name, metric_value FROM operational_metrics LIMIT 5"
    )
    assert len(rows) == 5
    assert "zone_code" in rows[0]


def test_execute_sql_avg_temperature(agent):
    rows = agent._execute_sql(
        "SELECT AVG(metric_value) as avg_temp FROM operational_metrics "
        "WHERE metric_name = 'temperature' LIMIT 1"
    )
    assert len(rows) == 1
    assert rows[0]["avg_temp"] is not None


def test_execute_sql_adds_limit_if_missing(agent):
    # Should not raise even without LIMIT; agent injects it
    rows = agent._execute_sql(
        "SELECT zone_code FROM operational_metrics"
    )
    assert len(rows) <= agent.settings.sql_max_rows
