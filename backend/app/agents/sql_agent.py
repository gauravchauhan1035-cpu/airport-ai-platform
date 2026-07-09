"""SQL agent: converts natural language to SQL, handles errors, and executes it safely."""

import logging
import re
import time
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.prompts.sql_prompt import build_sql_prompt
from app.services.llm_service import LLMService
from app.utils.input_sanitizer import detect_data_exfiltration

logger = logging.getLogger(__name__)

# Only SELECT statements are allowed
_SELECT_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)

# Maximum rows returned (hardened)
_MAX_ROWS = 20
_DEFAULT_LIMIT = 10


class SQLAgentError(Exception):
    """Raised when the SQL agent cannot produce a safe query."""


class SQLAgent:
    """Converts natural language questions to safe SELECT queries and executes them."""

    # Comprehensive blocklist — covers DDL, DML, SQLite-specific, and exploitation vectors
    _FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
        "EXEC", "EXECUTE", "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX",
        "GRANT", "REVOKE", "SAVEPOINT", "ROLLBACK", "COMMIT", "BEGIN",
    ]

    # System tables that must never be queried
    _BLOCKED_TABLES = [
        "sqlite_master", "sqlite_sequence", "sqlite_temp_master",
        "information_schema", "pg_catalog", "sys.",
        "users",  # Never allow AI to query user table
    ]

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.llm = LLMService()

    # ── Security validation ──────────────────────────────────────────────────

    def _validate_sql(self, sql: str) -> None:
        """Comprehensive SQL security validation.
        
        Raises SQLAgentError if the query is unsafe.
        """
        clean = sql.strip().rstrip(";")
        upper_sql = clean.upper()

        # 1. Must start with SELECT
        if not _SELECT_RE.match(clean):
            raise SQLAgentError("Only SELECT queries are permitted.")

        # 2. Block multiple statements (semicolons within the query)
        # Strip string literals first to avoid false positives
        stripped = re.sub(r"'[^']*'", "''", clean)
        if ";" in stripped:
            raise SQLAgentError("Multiple SQL statements are not allowed.")

        # 3. Block SQL comments (-- and /* */)
        if "--" in stripped or "/*" in stripped:
            raise SQLAgentError("SQL comments are not allowed.")

        # 4. Block forbidden keywords
        for kw in self._FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", upper_sql):
                raise SQLAgentError(f"Forbidden SQL keyword detected.")

        # 5. Block system table access
        for table in self._BLOCKED_TABLES:
            if table.upper() in upper_sql:
                raise SQLAgentError("Access to system tables is not permitted.")

        # 6. Block UNION (prevents UNION-based injection)
        if re.search(r"\bUNION\b", upper_sql):
            raise SQLAgentError("UNION queries are not permitted.")

        # 7. Block subqueries (nested SELECT)
        select_count = len(re.findall(r"\bSELECT\b", upper_sql))
        if select_count > 1:
            raise SQLAgentError("Nested subqueries are not permitted.")

        # 8. Only allow querying the operational_metrics table
        # Extract FROM clause and verify table name
        from_match = re.search(r"\bFROM\s+(\S+)", upper_sql)
        if from_match:
            table_name = from_match.group(1).strip("\"'`")
            if table_name != "OPERATIONAL_METRICS":
                raise SQLAgentError("Only the operational metrics data can be queried.")

    def _enforce_limit(self, sql: str) -> str:
        """Ensure a safe LIMIT clause is present and not excessive."""
        upper = sql.upper()
        
        # Check for existing LIMIT
        limit_match = re.search(r"\bLIMIT\s+(\d+)", upper)
        if limit_match:
            requested_limit = int(limit_match.group(1))
            if requested_limit > _MAX_ROWS:
                # Replace with max
                sql = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {_MAX_ROWS}", sql, flags=re.IGNORECASE)
        else:
            sql = f"{sql.rstrip(';')} LIMIT {_DEFAULT_LIMIT}"
        
        return sql

    def _execute_sql(self, sql: str) -> list[dict[str, Any]]:
        """Execute the SQL and return rows as list of dicts."""
        sql = self._enforce_limit(sql)

        result = self.db.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchmany(_MAX_ROWS)
        
        formatted_rows = []
        for row in rows:
            formatted_row = {}
            for col, val in zip(columns, row):
                if isinstance(val, float):
                    formatted_row[col] = round(val, 2)
                else:
                    formatted_row[col] = val
            formatted_rows.append(formatted_row)
            
        return formatted_rows

    # ── Public interface ──────────────────────────────────────────────────────

    def run(self, question: str) -> dict[str, Any]:
        """Convert a natural language question to SQL, execute it.

        Returns:
            {
                "question": str,
                "sql": str,
                "rows": list[dict],
                "row_count": int,
                "summary": str,
                "execution_time_ms": int,
            }
        """
        start = time.perf_counter()
        logger.info("SQL agent processing question (truncated): %.80s", question)

        # Pre-check: reject obvious data exfiltration attempts before even calling LLM
        if detect_data_exfiltration(question):
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            return {
                "question": question,
                "sql": "",
                "rows": [],
                "row_count": 0,
                "summary": "I cannot display the complete operational database. Please ask for specific metrics such as average temperature, humidity, or passenger count.",
                "execution_time_ms": elapsed_ms,
            }

        system_prompt, user_message = build_sql_prompt(question)
        
        sql = ""
        rows = []
        max_retries = 2
        last_error = ""

        # Self-correction loop
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info("SQL Agent retry %d/%d", attempt, max_retries)
                    # Sanitize error message for LLM — never expose internals
                    safe_error = "The previous SQL query was invalid. Generate a corrected query."
                    user_message += f"\n\n{safe_error}"

                llm_output = self.llm.generate(system_prompt, user_message, json_format=True)
                
                # Parse JSON
                try:
                    payload = json.loads(llm_output)
                    sql = payload.get("sql", "").strip()
                except json.JSONDecodeError:
                    raise SQLAgentError("Failed to parse query output.")

                if not sql:
                    raise SQLAgentError("No query was generated.")

                logger.info("Generated SQL (Attempt %d): %s", attempt + 1, sql)

                # Comprehensive security validation
                self._validate_sql(sql)

                # Execute
                rows = self._execute_sql(sql)
                
                # Success — break retry loop
                break
                
            except Exception as exc:
                last_error = str(exc)
                if attempt == max_retries:
                    logger.error("SQL agent failed after %d attempts", max_retries + 1)
                    # Return safe error, never expose SQL internals
                    elapsed_ms = int((time.perf_counter() - start) * 1000)
                    return {
                        "question": question,
                        "sql": sql,
                        "rows": [],
                        "row_count": 0,
                        "summary": "I was unable to retrieve the requested data. Please try rephrasing your question.",
                        "execution_time_ms": elapsed_ms,
                    }

        logger.info("SQL returned %d rows", len(rows))

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        
        temp_summary = f"Query returned {len(rows)} row(s)."
        if not rows:
            temp_summary = "No data found."
            
        return {
            "question": question,
            "sql": sql,
            "rows": rows,
            "row_count": len(rows),
            "summary": temp_summary, 
            "execution_time_ms": elapsed_ms,
        }
