"""Aggregator agent: synthesizes outputs from multiple agents into a single response."""

import logging
import time
import json

from app.services.llm_service import LLMService
from app.prompts.aggregator_prompt import build_aggregator_prompt

logger = logging.getLogger(__name__)


class AggregatorAgent:
    """Combines outputs from SQL, RAG, and Chat agents into a cohesive response."""

    def __init__(self) -> None:
        self.llm = LLMService()

    def run(
        self, 
        question: str, 
        sql_result: dict | None = None, 
        rag_result: dict | None = None, 
        chat_result: str | None = None,
        history: list[dict[str, str]] | None = None
    ) -> str:
        """
        Synthesize multiple agent outputs into a final answer.
        """
        start = time.perf_counter()
        logger.info("Aggregator agent synthesizing responses...")

        system_prompt, user_message = build_aggregator_prompt(
            question=question,
            sql_result=sql_result,
            rag_result=rag_result,
            chat_result=chat_result
        )

        answer = ""
        try:
            # We strictly enforce JSON outputs for reliability
            response_text = self.llm.generate(
                system_prompt=system_prompt,
                user_message=user_message,
                history=history,
                json_format=True
            )
            payload = json.loads(response_text)
            answer = payload.get("answer", "I apologize, but I could not synthesize the retrieved information.")
        except Exception as exc:
            logger.error("Aggregator agent failed: %s", exc)
            
            # Fallback to simple concatenation if the LLM fails completely
            parts = []
            if sql_result and sql_result.get("rows"):
                parts.append("Data retrieved successfully, but synthesis failed.")
            if rag_result and rag_result.get("answer"):
                parts.append(rag_result["answer"])
            if chat_result:
                parts.append(chat_result)
            answer = "\n\n".join(parts) if parts else "System error during aggregation."

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Aggregator agent completed in %dms", elapsed_ms)
        
        return answer
