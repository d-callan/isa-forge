"""Ollama LLM client implementation for local models."""

from typing import Any

import httpx

from isaforge.agents.llm.base import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolCall,
)
from isaforge.core.config import settings
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class OllamaClient(LLMClient):
    """LLM client for local Ollama models."""

    def __init__(
        self,
        model: str | None = None,
        session_id: str | None = None,
        base_url: str | None = None,
    ):
        """Initialize the Ollama client.

        Args:
            model: Model identifier (defaults to 'llama3.1').
            session_id: Optional session ID for tracking.
            base_url: Ollama server URL (defaults to settings.ollama_base_url).
        """
        model = model or "llama3.1"
        super().__init__(model=model, session_id=session_id)

        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def _call(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make the API call to Ollama.

        Args:
            messages: Conversation messages.
            tools: Optional tool definitions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_msg = {
                "role": msg.role.value,
                "content": msg.content,
            }
            ollama_messages.append(ollama_msg)

        # Build request payload
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        # Make the API call
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Parse response
        content = data.get("message", {}).get("content")
        tool_calls = []

        # Parse tool calls if present
        message_tool_calls = data.get("message", {}).get("tool_calls", [])
        for i, tc in enumerate(message_tool_calls):
            func = tc.get("function", {})
            tool_calls.append(
                LLMToolCall(
                    id=f"call_{i}",
                    name=func.get("name", ""),
                    arguments=func.get("arguments", {}),
                )
            )

        # Get token counts
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self.model,
            finish_reason=data.get("done_reason", ""),
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tool definitions to Ollama format.

        Ollama uses the same format as OpenAI for tools.

        Args:
            tools: Tool definitions in OpenAI format.

        Returns:
            Tool definitions (same format for Ollama).
        """
        return tools

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "ollama"
