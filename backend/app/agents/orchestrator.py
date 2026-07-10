"""Workflow orchestrator for executing multi-agent DAG plans."""

import logging
import time
from typing import Any
from sqlalchemy.orm import Session

from app.services.memory_service import MemoryService
from app.agents.router_agent import IntentRouter

logger = logging.getLogger(__name__)

import asyncio
from app.database.session import SessionLocal

class WorkflowOrchestrator:
    """Manages the execution of the IntentRouter plan."""

    def __init__(self, db: Session):
        self.db = db
        self.router = IntentRouter()
        self.memory = MemoryService(db)

    def _run_sql(self, question: str, history: list) -> dict:
        db = SessionLocal()
        try:
            from app.agents.sql_agent import SQLAgent
            return SQLAgent(db).run(question, history=history)
        except Exception as exc:
            logger.error("SQL Agent failed: %s", exc)
            return {"summary": f"SQL Error: {str(exc)}"}
        finally:
            db.close()

    def _run_rag(self, question: str, history: list) -> dict:
        db = SessionLocal()
        try:
            from app.rag.rag_agent import RAGAgent
            return RAGAgent(db).search(question, history=history)
        except Exception as exc:
            logger.error("RAG Agent failed: %s", exc)
            return {"error": str(exc)}
        finally:
            db.close()

    def _run_chat(self, question: str, history: list) -> str:
        try:
            from app.agents.chat_agent import ChatAgent
            return ChatAgent().run(question, history=history).get("answer")
        except Exception as exc:
            logger.error("Chat Agent failed: %s", exc)
            return "Chat module is currently unavailable."

    async def execute_async(self, question: str, session_id: str | None = None) -> dict[str, Any]:
        """
        1. Fetch history.
        2. Route intent (returns JSON plan).
        3. Execute requested agents (in PARALLEL).
        4. Aggregate results.
        5. Save memory.
        """
        start = time.perf_counter()
        
        # 1. Fetch History
        history = self.memory.get_history(session_id)
        
        # 2. Get Execution Plan
        plan = await asyncio.to_thread(self.router.determine_plan, question, history)
        agents_to_run = plan.get("agents", ["CHAT"])
        logger.info(f"Execution Plan: {plan}")

        sql_result: dict | None = None
        rag_result: dict | None = None
        chat_result: str | None = None

        # 3. Execute Agents in PARALLEL using to_thread
        tasks = []
        if "SQL" in agents_to_run:
            tasks.append(("SQL", asyncio.to_thread(self._run_sql, question, history)))
        if "RAG" in agents_to_run:
            tasks.append(("RAG", asyncio.to_thread(self._run_rag, question, history)))
        if "CHAT" in agents_to_run:
            tasks.append(("CHAT", asyncio.to_thread(self._run_chat, question, history)))

        # Wait for all scheduled tasks to complete
        results = await asyncio.gather(*(t for _, t in tasks))
        
        # Unpack results back to respective variables
        for (agent_type, _), res in zip(tasks, results):
            if agent_type == "SQL":
                sql_result = res
            elif agent_type == "RAG":
                rag_result = res
            elif agent_type == "CHAT":
                chat_result = res

        # 4. Aggregate Results
        # Fast-path for empty RAG to prevent hallucination in tiny models
        if agents_to_run == ["RAG"] and rag_result and not rag_result.get("results"):
            final_answer = rag_result.get("answer", "No documents found.")
        elif agents_to_run == ["SQL"] and sql_result and not sql_result.get("rows"):
            final_answer = "I could not find any live operational data to answer your question."
        else:
            from app.agents.aggregator_agent import AggregatorAgent
            final_answer = await asyncio.to_thread(
                AggregatorAgent().run,
                question=question,
                sql_result=sql_result,
                rag_result=rag_result,
                chat_result=chat_result,
                history=history
            )

        # 5. Save Memory
        self.memory.add_message(session_id, "user", question)
        self.memory.add_message(session_id, "assistant", final_answer)

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Return backward compatible format for frontend (until Step 8)
        return {
            "question": question,
            "answer": final_answer,
            "route": ",".join(agents_to_run),  # Temporary mapping
            "sql": sql_result.get("sql") if sql_result else None,
            "sql_rows": sql_result.get("rows") if sql_result else None,
            "row_count": sql_result.get("row_count") if sql_result else None,
            "retrieved_chunks": rag_result.get("results") if rag_result else None,
            "execution_time_ms": elapsed_ms,
        }
