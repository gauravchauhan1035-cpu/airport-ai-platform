"""Query endpoint – AI router dispatching to SQL, RAG, or both."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database.session import get_db
from app.models.user import User, UserRole
from app.utils.input_sanitizer import sanitize_user_input, detect_prompt_injection, detect_data_exfiltration
from app.utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    session_id: str | None = Field(
        default=None, description="Optional session ID for conversation memory"
    )


class QueryResponse(BaseModel):
    question: str
    answer: str
    route: str  # "SQL", "RAG", or "BOTH"
    sql: str | None = None
    sql_rows: list[dict] | None = None
    row_count: int | None = None
    retrieved_chunks: list[dict] | None = None
    execution_time_ms: int = 0


@router.post("", response_model=QueryResponse)
@limiter.limit("30/minute")
async def query(
    request: Request,
    payload: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.ANALYST)),
) -> QueryResponse:
    """Route a natural language question to SQL, RAG, or both agents.

    - SQL: metrics and operational data questions
    - RAG: procedural and document-based questions
    - BOTH: questions that require both data and context
    """
    from app.agents.orchestrator import WorkflowOrchestrator

    # Input sanitization — strip injection delimiters
    sanitized_question = sanitize_user_input(payload.question)

    # Detect prompt injection attempts
    if detect_prompt_injection(sanitized_question):
        logger.warning("Prompt injection attempt blocked from user: %s", current_user.username)
        return QueryResponse(
            question=payload.question,
            answer="I cannot disclose internal implementation details.",
            route="BLOCKED",
            execution_time_ms=0,
        )

    # Detect data exfiltration / schema enumeration attempts
    if detect_data_exfiltration(sanitized_question):
        logger.warning("Data exfiltration attempt blocked from user: %s", current_user.username)
        return QueryResponse(
            question=payload.question,
            answer="I cannot disclose internal implementation details.",
            route="BLOCKED",
            execution_time_ms=0,
        )

    logger.info(
        "Query from %s (role=%s, session=%s)",
        current_user.username,
        current_user.role,
        payload.session_id,
    )

    try:
        result = await WorkflowOrchestrator(db).execute_async(
            question=sanitized_question,
            session_id=payload.session_id,
        )
    except Exception as exc:
        logger.error("Orchestrator error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query service temporarily unavailable.",
        ) from exc

    # SECURITY: Only Admin users can see debug fields (SQL, rows, chunks)
    is_admin = current_user.role == UserRole.ADMIN.value

    return QueryResponse(
        question=result["question"],
        answer=result["answer"],
        route=result["route"],
        sql=result.get("sql") if is_admin else None,
        sql_rows=result.get("sql_rows") if is_admin else None,
        row_count=result.get("row_count") if is_admin else None,
        retrieved_chunks=result.get("retrieved_chunks") if is_admin else None,
        execution_time_ms=result["execution_time_ms"],
    )
