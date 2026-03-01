"""Google Gemini LLM client implementation."""

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


class GoogleClient(LLMClient):
    """LLM client for Google Gemini models."""

    def __init__(
        self,
        model: str | None = None,
        session_id: str | None = None,
        api_key: str | None = None,
    ):
        """Initialize the Google client.

        Args:
            model: Model identifier (defaults to 'gemini-1.5-pro').
            session_id: Optional session ID for tracking.
            api_key: API key (defaults to settings.google_api_key).
        """
        model = model or "gemini-1.5-pro"
        super().__init__(model=model, session_id=session_id)

        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise ValueError("Google API key is required")

        self._client = None

    def _get_client(self):
        """Get or create the Google Generative AI client."""
        if self._client is None:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError as e:
                raise ImportError(
                    "google-generativeai package is required. "
                    "Install with: pip install google-generativeai"
                ) from e
        return self._client

    async def _call(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make the API call to Google Gemini.

        Args:
            messages: Conversation messages.
            tools: Optional tool definitions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        client = self._get_client()

        # Convert messages to Gemini format
        system_instruction = None
        gemini_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            elif msg.role == MessageRole.USER:
                gemini_messages.append({"role": "user", "parts": [msg.content]})
            elif msg.role == MessageRole.ASSISTANT:
                gemini_messages.append({"role": "model", "parts": [msg.content]})
            elif msg.role == MessageRole.TOOL:
                gemini_messages.append({
                    "role": "function",
                    "parts": [{
                        "function_response": {
                            "name": msg.tool_call_id or "unknown",
                            "response": {"result": msg.content},
                        }
                    }],
                })

        # Build generation config
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        # Build request kwargs
        kwargs: dict[str, Any] = {
            "contents": gemini_messages,
            "generation_config": generation_config,
        }

        if system_instruction:
            kwargs["system_instruction"] = system_instruction

        if tools:
            kwargs["tools"] = self._convert_tools(tools)

        # Make the API call (Gemini uses sync API, wrap in async)
        import asyncio

        response = await asyncio.to_thread(
            client.generate_content,
            **kwargs,
        )

        # Parse response
        content = None
        tool_calls = []

        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    content = part.text
                elif hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_calls.append(
                        LLMToolCall(
                            id=f"call_{len(tool_calls)}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )

        # Get token counts
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, "usage_metadata"):
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model=self.model,
            finish_reason=candidate.finish_reason.name if response.candidates else "",
        )

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style tool definitions to Gemini format.

        Args:
            tools: Tool definitions in OpenAI format.

        Returns:
            Tool definitions in Gemini format.
        """
        gemini_tools = []
        function_declarations = []

        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                function_declarations.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                function_declarations.append(tool)

        if function_declarations:
            gemini_tools.append({"function_declarations": function_declarations})

        return gemini_tools

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "google"
