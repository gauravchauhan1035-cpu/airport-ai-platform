"""Service for interacting with the Ollama LLM."""

import logging
import json
from typing import Any
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

class LLMService:
    """Centralized service for calling the local Ollama LLM."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"{self.settings.ollama_base_url}/api/chat"
        self.model = self.settings.ollama_model

    def generate(
        self, 
        system_prompt: str, 
        user_message: str, 
        history: list[dict[str, str]] | None = None,
        json_format: bool = False,
        timeout: float = 300.0
    ) -> str:
        """Call the LLM with an optional conversation history and JSON mode toggle."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": user_message})

        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": messages,
            "options": {
                "temperature": 0.0 if json_format else 0.7  # Deterministic for JSON
            }
        }
        
        if json_format:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(self.base_url, json=payload)
                response.raise_for_status()
                
            return response.json()["message"]["content"].strip()
            
        except httpx.TimeoutException as exc:
            logger.error("LLM request timed out after %s seconds", timeout)
            raise RuntimeError(f"LLM request timed out: {exc}") from exc
        except Exception as exc:
            logger.error("LLM request failed: %s", exc)
            raise RuntimeError(f"LLM request failed: {exc}") from exc
