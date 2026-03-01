"""Anthropic Claude LLM client implementation."""

from typing import Any

from isaforge.agents.llm.base import (
    LLMClient,
    LLMMessage,
    LLMResponse,
    LLMToolCall,
    MessageRole,
)
from isaforge.core.config import settings
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class AnthropicClient(LLMClient):
    """LLM client for Anthropic Claude models."""

    def __init__(
        self,
        model: str | None = None,
        session_id: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the Anthropic client.

        Args:
            model: Model identifier (defaults to settings.llm_model).
            session_id: Optional session ID for tracking.
            api_key: API key (defaults to settings.anthropic_api_key).
        """
        model = model or settings.llm_model
        super().__init__(model=model, session_id=session_id)

        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        self._client = None

    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError as e:
                raise ImportError(
                    "anthropic package is required. Install with: pip install anthropic"
                ) from e
        return self._client

    async def _call(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make the API call to Anthropic.

        Args:
            messages: Conversation messages.
            tools: Optional tool definitions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        client = self._get_client()

        # Extract system message and convert messages
        system_content = None
        api_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_content = msg.content
            elif msg.role == MessageRole.TOOL:
                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }
                    ],
                })
            else:
                api_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        # Build request kwargs
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_content:
            kwargs["system"] = system_content

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        # Make the API call
        response = await client.messages.create(**kwargs)

        # Parse response
        content = None
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    LLMToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            model=response.model,
            finish_reason=response.stop_reason or "",
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tool definitions to Anthropic format.

        Args:
            tools: Tool definitions in OpenAI format.

        Returns:
            Tool definitions in Anthropic format.
        """
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                anthropic_tools.append(tool)
        return anthropic_tools

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "anthropic"
