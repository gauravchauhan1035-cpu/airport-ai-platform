"""Chat agent: handles general conversation, reasoning, and summarization."""

import logging
import time
import json
from typing import Any

from app.services.llm_service import LLMService
from app.prompts.chat_prompt import build_chat_prompt

logger = logging.getLogger(__name__)


class ChatAgent:
    """Handles general conversational queries without accessing external data."""

    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, question: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """
        Respond to a conversational question using LLM with context history.
        
        Args:
            question: Natural language question from the user.
            history: Previous conversation messages (from MemoryService).

        Returns:
            {
                "question": str,
                "answer": str,
                "execution_time_ms": int,
            }
        """
        start = time.perf_counter()
        logger.info("Chat agent processing question: %s", question)

        system_prompt = build_chat_prompt()
        answer = ""

        try:
            # We strictly enforce JSON outputs for reliability
            response_text = self.llm.generate(
                system_prompt=system_prompt,
                user_message=question,
                history=history,
                json_format=True
            )
            payload = json.loads(response_text)
            answer = payload.get("answer", "I apologize, but I encountered an error generating a response.")
        except Exception as exc:
            logger.error("Chat agent failed: %s", exc)
            answer = "I apologize, but I am currently unavailable. Please try again later."

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Chat agent completed in %dms", elapsed_ms)
        
        return {
            "question": question,
            "answer": answer,
            "execution_time_ms": elapsed_ms,
        }
