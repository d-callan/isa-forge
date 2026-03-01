"""LLM client implementations for ISA-Forge."""

from isaforge.agents.llm.base import (
    LLMCallRecord,
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    MessageRole,
)
from isaforge.core.config import settings


def get_llm_client(session_id: str | None = None) -> LLMClient:
    """Get an LLM client based on settings.

    Args:
        session_id: Optional session ID for tracking.

    Returns:
        Configured LLM client.

    Raises:
        ValueError: If provider is not supported.
    """
    provider = settings.llm_provider

    if provider == "anthropic":
        from isaforge.agents.llm.anthropic import AnthropicClient

        return AnthropicClient(session_id=session_id)
    elif provider == "google":
        from isaforge.agents.llm.google import GoogleClient

        return GoogleClient(session_id=session_id)
    elif provider == "ollama":
        from isaforge.agents.llm.ollama import OllamaClient

        return OllamaClient(session_id=session_id)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


__all__ = [
    "LLMCallRecord",
    "LLMClient",
    "LLMMessage",
    "LLMResponse",
    "LLMToolCall",
    "MessageRole",
    "get_llm_client",
]
