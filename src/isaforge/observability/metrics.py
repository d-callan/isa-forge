"""Metrics collection for ISA-Forge operations."""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    name: str
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000

    def complete(self, success: bool = True, error: str | None = None) -> None:
        """Mark the operation as complete.

        Args:
            success: Whether the operation succeeded.
            error: Error message if failed.
        """
        self.end_time = time.time()
        self.success = success
        self.error = error


@dataclass
class SessionMetrics:
    """Aggregated metrics for a session."""

    session_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)

    # LLM metrics
    total_llm_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_llm_latency_ms: float = 0.0

    # Tool metrics
    total_tool_calls: int = 0
    tool_call_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tool_success_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tool_failure_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_tool_latency_ms: float = 0.0

    # Field metrics
    total_fields: int = 0
    auto_accepted_fields: int = 0
    user_edited_fields: int = 0
    flagged_fields: int = 0

    # Conversation metrics
    turn_count: int = 0
    user_messages: int = 0
    assistant_messages: int = 0

    def record_llm_call(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
    ) -> None:
        """Record an LLM call.

        Args:
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            latency_ms: Latency in milliseconds.
        """
        self.total_llm_calls += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_llm_latency_ms += latency_ms

    def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record a tool call.

        Args:
            tool_name: Name of the tool.
            success: Whether the call succeeded.
            latency_ms: Latency in milliseconds.
        """
        self.total_tool_calls += 1
        self.tool_call_counts[tool_name] += 1
        if success:
            self.tool_success_counts[tool_name] += 1
        else:
            self.tool_failure_counts[tool_name] += 1
        self.total_tool_latency_ms += latency_ms

    def record_field_decision(
        self,
        action: str,
    ) -> None:
        """Record a field decision.

        Args:
            action: The user action (auto_accepted, user_edited, flagged, etc.).
        """
        self.total_fields += 1
        if action == "auto_accepted":
            self.auto_accepted_fields += 1
        elif action == "user_edited":
            self.user_edited_fields += 1
        elif action == "flagged":
            self.flagged_fields += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary.

        Returns:
            Dictionary representation of metrics.
        """
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "llm": {
                "total_calls": self.total_llm_calls,
                "total_prompt_tokens": self.total_prompt_tokens,
                "total_completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
                "total_latency_ms": self.total_llm_latency_ms,
                "avg_latency_ms": (
                    self.total_llm_latency_ms / self.total_llm_calls
                    if self.total_llm_calls > 0
                    else 0
                ),
            },
            "tools": {
                "total_calls": self.total_tool_calls,
                "call_counts": dict(self.tool_call_counts),
                "success_counts": dict(self.tool_success_counts),
                "failure_counts": dict(self.tool_failure_counts),
                "total_latency_ms": self.total_tool_latency_ms,
            },
            "fields": {
                "total": self.total_fields,
                "auto_accepted": self.auto_accepted_fields,
                "user_edited": self.user_edited_fields,
                "flagged": self.flagged_fields,
            },
            "conversation": {
                "turn_count": self.turn_count,
                "user_messages": self.user_messages,
                "assistant_messages": self.assistant_messages,
            },
        }


class MetricsCollector:
    """Collector for session metrics."""

    _sessions: dict[str, SessionMetrics] = {}

    @classmethod
    def get_or_create(cls, session_id: str) -> SessionMetrics:
        """Get or create metrics for a session.

        Args:
            session_id: The session ID.

        Returns:
            Session metrics instance.
        """
        if session_id not in cls._sessions:
            cls._sessions[session_id] = SessionMetrics(session_id=session_id)
        return cls._sessions[session_id]

    @classmethod
    def get(cls, session_id: str) -> SessionMetrics | None:
        """Get metrics for a session.

        Args:
            session_id: The session ID.

        Returns:
            Session metrics or None if not found.
        """
        return cls._sessions.get(session_id)

    @classmethod
    def remove(cls, session_id: str) -> None:
        """Remove metrics for a session.

        Args:
            session_id: The session ID.
        """
        cls._sessions.pop(session_id, None)

    @classmethod
    def clear(cls) -> None:
        """Clear all session metrics."""
        cls._sessions.clear()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str, metadata: dict[str, Any] | None = None):
        """Initialize timer.

        Args:
            name: Name of the operation being timed.
            metadata: Optional metadata to include in logs.
        """
        self.name = name
        self.metadata = metadata or {}
        self.metrics: OperationMetrics | None = None

    def __enter__(self) -> "Timer":
        """Start timing."""
        self.metrics = OperationMetrics(name=self.name, metadata=self.metadata)
        logger.debug("operation_started", operation=self.name, **self.metadata)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and log results."""
        if self.metrics:
            success = exc_type is None
            error = str(exc_val) if exc_val else None
            self.metrics.complete(success=success, error=error)

            log_method = logger.debug if success else logger.warning
            log_method(
                "operation_completed",
                operation=self.name,
                duration_ms=self.metrics.duration_ms,
                success=success,
                error=error,
                **self.metadata,
            )

    @property
    def duration_ms(self) -> float:
        """Get current duration in milliseconds."""
        if self.metrics:
            return self.metrics.duration_ms
        return 0.0
