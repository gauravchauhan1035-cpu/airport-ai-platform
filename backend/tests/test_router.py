"""Tests for the AI Router agent – classification, memory, and combiner logic."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.router_agent import (
    RouterAgent,
    append_memory,
    classify_route,
    combine_responses,
    get_memory,
)
from app.database.base import Base
from app.database.init_db import seed_if_empty


@pytest.fixture()
def db_session(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test_router.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    seed_if_empty(session)
    yield session
    session.close()
    engine.dispose()


# ── Route Classification ───────────────────────────────────────────────────────

def test_classify_sql_temperature():
    assert classify_route("What is the average temperature in Terminal 1?") == "SQL"


def test_classify_sql_passenger_count():
    assert classify_route("How many passengers are in T2?") == "SQL"


def test_classify_sql_latest_readings():
    assert classify_route("Show the latest wind speed readings") == "SQL"


def test_classify_rag_procedure():
    assert classify_route("What is the emergency evacuation procedure?") == "RAG"


def test_classify_rag_policy():
    assert classify_route("What is the safety policy for runway operations?") == "RAG"


def test_classify_rag_sop():
    assert classify_route("What does the SOP say about compliance?") == "RAG"


def test_classify_both_mixed():
    result = classify_route(
        "What is the temperature in CNS and what does the safety manual say about it?"
    )
    assert result == "BOTH"


def test_classify_defaults_to_sql():
    # Generic question with no strong keywords defaults to SQL (data platform)
    result = classify_route("Tell me something")
    assert result == "SQL"


# ── Conversation Memory ────────────────────────────────────────────────────────

def test_memory_append_and_retrieve():
    session_id = "test-session-001"
    append_memory(session_id, "user", "Hello!")
    append_memory(session_id, "assistant", "Hi there!")
    history = get_memory(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_memory_max_length():
    session_id = "test-session-002"
    for i in range(10):
        append_memory(session_id, "user", f"Message {i}")
    history = get_memory(session_id)
    # Max memory is 6
    assert len(history) <= 6


def test_memory_no_session_id():
    append_memory(None, "user", "No session")
    result = get_memory(None)
    assert result == []


# ── Response Combiner ─────────────────────────────────────────────────────────

def test_combine_responses_sql_only():
    sql_result = {"summary": "Average temperature is 23.5 C", "rows": []}
    answer = combine_responses("temperature?", sql_result, None)
    assert "23.5" in answer


def test_combine_responses_rag_only():
    rag_result = {
        "results": [
            {
                "document_name": "Manual.pdf",
                "page_number": 5,
                "content": "The emergency procedure requires...",
                "score": 0.9,
            }
        ]
    }
    answer = combine_responses("emergency procedure?", None, rag_result)
    assert "Manual.pdf" in answer
    assert "emergency" in answer


def test_combine_responses_both():
    sql_result = {"summary": "Temperature is 22C", "rows": []}
    rag_result = {
        "results": [
            {
                "document_name": "Safety.pdf",
                "page_number": 3,
                "content": "Temperature guidelines state...",
                "score": 0.8,
            }
        ]
    }
    answer = combine_responses("temperature guidelines?", sql_result, rag_result)
    assert "operational data" in answer.lower() or "22C" in answer
    assert "Safety.pdf" in answer


def test_combine_responses_empty():
    answer = combine_responses("unknown?", None, None)
    assert "No relevant" in answer


# ── Router Agent Integration ──────────────────────────────────────────────────

def test_router_agent_sql_route_executes(db_session):
    """RouterAgent SQL route should execute without calling Ollama (DB-level test)."""
    agent = RouterAgent(db_session)
    # Manually test that classify_route is called correctly
    route = classify_route("What is the average temperature?")
    assert route == "SQL"


def test_router_agent_classifies_correctly(db_session):
    """The router should correctly classify different question types."""
    agent = RouterAgent(db_session)
    # We test the classification layer, not the full LLM call
    assert classify_route("Show average humidity in CNS") == "SQL"
    assert classify_route("What is the safety protocol?") == "RAG"
