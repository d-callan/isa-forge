"""Base LLM client with logging and tracking."""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from isaforge.agents.prompts.versioning import compute_hash
from isaforge.observability.logger import get_logger
from isaforge.observability.metrics import MetricsCollector

logger = get_logger(__name__)


class MessageRole(str, Enum):
    """Role of a message in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """A message in an LLM conversation."""

    role: MessageRole
    content: str
    tool_call_id: str | None = None
    tool_calls: list["LLMToolCall"] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        result: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


@dataclass
class LLMToolCall:
    """A tool call requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class LLMResponse:
    """Response from an LLM call."""

    content: str | None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = ""
    finish_reason: str = ""

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.prompt_tokens + self.completion_tokens

    @property
    def has_tool_calls(self) -> bool:
        """Whether the response contains tool calls."""
        return len(self.tool_calls) > 0


@dataclass
class LLMCallRecord:
    """Record of an LLM call for tracking."""

    id: str
    session_id: str | None
    task: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    system_prompt_hash: str | None
    user_prompt_hash: str | None
    tool_calls: list[dict[str, Any]]
    error: str | None = None


class LLMClient(ABC):
    """Abstract base class for LLM clients.

    Provides automatic logging, metrics tracking, and prompt hash recording.
    """

    def __init__(self, model: str, session_id: str | None = None):
        """Initialize the client.

        Args:
            model: Model identifier.
            session_id: Optional session ID for tracking.
        """
        self.model = model
        self.session_id = session_id
        self._metrics = MetricsCollector.get_or_create(session_id) if session_id else None

    @abstractmethod
    async def _call(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make the actual API call. Implemented by subclasses.

        Args:
            messages: Conversation messages.
            tools: Optional tool definitions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        pass

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        task: str = "chat",
    ) -> tuple[LLMResponse, LLMCallRecord]:
        """Send a chat request with automatic logging.

        Args:
            messages: Conversation messages.
            tools: Optional tool definitions.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            task: Task identifier for logging.

        Returns:
            Tuple of (LLMResponse, LLMCallRecord).
        """
        call_id = str(uuid.uuid4())
        start_time = time.time()
        error_msg = None

        # Compute prompt hashes
        system_prompt_hash = None
        user_prompt_hash = None
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt_hash = compute_hash(msg.content)
            elif msg.role == MessageRole.USER:
                user_prompt_hash = compute_hash(msg.content)

        try:
            response = await self._call(
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "llm_call_error",
                call_id=call_id,
                model=self.model,
                task=task,
                error=error_msg,
            )
            raise

        latency_ms = int((time.time() - start_time) * 1000)

        # Create call record
        record = LLMCallRecord(
            id=call_id,
            session_id=self.session_id,
            task=task,
            model=self.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=latency_ms,
            system_prompt_hash=system_prompt_hash,
            user_prompt_hash=user_prompt_hash,
            tool_calls=[tc.to_dict() for tc in response.tool_calls],
            error=error_msg,
        )

        # Log the call
        logger.info(
            "llm_call_completed",
            call_id=call_id,
            model=self.model,
            task=task,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            latency_ms=latency_ms,
            tool_call_count=len(response.tool_calls),
        )

        # Update metrics if available
        if self._metrics:
            self._metrics.record_llm_call(
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                latency_ms=latency_ms,
            )

        return response, record

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name (e.g., 'anthropic', 'google', 'ollama')."""
        pass
