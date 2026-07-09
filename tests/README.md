# Test Suite Documentation

This document outlines the testing strategy and coverage for the Airport AI Platform. The backend relies on `pytest` for unit and integration testing.

## Running Tests

To run the full backend test suite:

```bash
cd backend
pytest -v
```

## Existing Test Coverage (Backend)

The current test suite (`backend/tests/`) covers the core logic and safety mechanisms of the application.

### 1. Authentication Tests (`test_auth.py`)
- **Coverage:** Login generation, JWT creation, JWT decoding, and Role-Based Access Control (RBAC).
- **Key Assertions:** Verifies that a user with a `viewer` role cannot access endpoints requiring an `admin` role, and ensures expired or malformed JWTs are strictly rejected by the dependency injectors.

### 2. Database Tests (`test_database.py`)
- **Coverage:** SQLAlchemy session management and basic CRUD operations.
- **Key Assertions:** Ensures the SQLite database initializes correctly and the tables (`users`, `operational_metrics`, etc.) are created successfully.

### 3. Core API Tests (`test_health.py`, `test_metrics_api.py`, `test_dashboard.py`)
- **Coverage:** Standard REST endpoints.
- **Key Assertions:** Validates JSON serialization, HTTP status codes (200 OK vs 401 Unauthorized), and pagination limits for metric retrieval.

### 4. Router Agent Tests (`test_router.py`)
- **Coverage:** The Intent Routing logic (the brain of the platform).
- **Key Assertions:** Mocks the LLM response to ensure the application correctly parses the JSON array output (e.g., `["SQL"]`, `["RAG"]`) and triggers the correct underlying agents. Ensures malformed LLM outputs fallback to safe defaults.

### 5. SQL Agent & Security Tests (`test_sql_agent.py`)
- **Coverage:** The read-only SQL generation and execution flow.
- **Key Assertions (Security):** Explicitly verifies the `_validate_sql()` method blocks `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `PRAGMA` commands. It also asserts that any attempt to query the `users` table or system master tables throws a security exception.

### 6. RAG Pipeline Tests (`test_rag.py`)
- **Coverage:** The retrieval mechanisms for FAISS and SQLite.
- **Key Assertions:** Mocks the embedding generation to ensure the top-K retrieval logic correctly queries FAISS, and verifies that the retrieved vector IDs successfully join with the SQLite `document_chunks` table to rebuild the raw text payload.

## Future Testing Scope (Not Yet Implemented)

### Frontend Tests (Next.js)
Currently, the frontend lacks automated testing. Future implementations should include:
- **Jest / React Testing Library:** Unit testing for individual React components (e.g., ensuring the chat bubble renders correctly based on the `role` prop).
- **Cypress / Playwright:** End-to-End (E2E) testing covering the login flow, navigating to the dashboard, and executing a test query in the AI Assistant.

### Knowledge Base Upload Tests
While RAG retrieval is tested, the file upload and chunking pipeline requires integration tests:
- Validating PDF MIME types are accepted and arbitrary files (e.g., `.exe`) are rejected.
- Asserting that a 1500-character string is correctly split into the expected number of chunks based on the `rag_chunk_size` configuration.
