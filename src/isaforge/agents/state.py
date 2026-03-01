"""Conversation state management for the agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from isaforge.core.config import settings
from isaforge.core.constants import SessionStatus, TerminationReason
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationState:
    """State of an ISA-Tab generation conversation."""

    session_id: str
    bioproject_id: str | None = None
    local_metadata_paths: list[str] = field(default_factory=list)
    output_path: str | None = None

    # Field tracking
    fields_resolved: set[str] = field(default_factory=set)
    fields_pending: set[str] = field(default_factory=set)
    retry_counts: dict[str, int] = field(default_factory=dict)

    # Conversation tracking
    turn_count: int = 0
    tool_calls_this_turn: int = 0
    last_user_input_time: datetime | None = None
    user_requested_exit: bool = False

    # Token tracking
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0

    # Status
    status: SessionStatus = SessionStatus.ACTIVE
    termination_reason: TerminationReason | None = None

    # Data collected
    metadata: dict[str, Any] = field(default_factory=dict)
    publications: list[dict[str, Any]] = field(default_factory=list)
    ontology_mappings: dict[str, Any] = field(default_factory=dict)

    def mark_field_resolved(self, field_path: str) -> None:
        """Mark a field as resolved.

        Args:
            field_path: Path to the field.
        """
        self.fields_resolved.add(field_path)
        self.fields_pending.discard(field_path)
        logger.debug("field_resolved", field_path=field_path)

    def mark_field_pending(self, field_path: str) -> None:
        """Mark a field as pending resolution.

        Args:
            field_path: Path to the field.
        """
        if field_path not in self.fields_resolved:
            self.fields_pending.add(field_path)

    def increment_retry(self, field_path: str) -> int:
        """Increment retry count for a field.

        Args:
            field_path: Path to the field.

        Returns:
            New retry count.
        """
        self.retry_counts[field_path] = self.retry_counts.get(field_path, 0) + 1
        return self.retry_counts[field_path]

    def get_retry_count(self, field_path: str) -> int:
        """Get retry count for a field.

        Args:
            field_path: Path to the field.

        Returns:
            Current retry count.
        """
        return self.retry_counts.get(field_path, 0)

    def start_turn(self) -> None:
        """Start a new conversation turn."""
        self.turn_count += 1
        self.tool_calls_this_turn = 0
        logger.debug("turn_started", turn_count=self.turn_count)

    def record_tool_call(self) -> None:
        """Record a tool call in this turn."""
        self.tool_calls_this_turn += 1

    def record_user_input(self) -> None:
        """Record that user provided input."""
        self.last_user_input_time = datetime.utcnow()

    def record_tokens(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage.

        Args:
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
        """
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

    def is_stuck(self) -> bool:
        """Check if the conversation is stuck.

        Returns:
            True if stuck (all pending fields at max retries).
        """
        if not self.fields_pending:
            return False

        return all(
            self.retry_counts.get(f, 0) >= settings.max_retries_per_field
            for f in self.fields_pending
        )

    def all_required_fields_resolved(self) -> bool:
        """Check if all required fields are resolved.

        Returns:
            True if no pending fields remain.
        """
        return len(self.fields_pending) == 0

    def can_continue(self) -> bool:
        """Check if the conversation can continue.

        Returns:
            True if conversation should continue.
        """
        if self.user_requested_exit:
            return False
        if self.turn_count >= settings.max_conversation_turns:
            return False
        if self.is_stuck():
            return False
        return True

    def should_terminate(self) -> tuple[bool, TerminationReason | None]:
        """Check if the conversation should terminate.

        Returns:
            Tuple of (should_terminate, reason).
        """
        # Success: All required fields resolved
        if self.all_required_fields_resolved() and self.fields_resolved:
            return True, TerminationReason.SUCCESS

        # User requested exit
        if self.user_requested_exit:
            return True, TerminationReason.USER_EXIT

        # Stuck: No progress possible
        if self.is_stuck():
            return True, TerminationReason.STUCK

        # Timeout: Exceeded max turns
        if self.turn_count >= settings.max_conversation_turns:
            return True, TerminationReason.MAX_TURNS_EXCEEDED

        return False, None

    def can_call_tool(self) -> bool:
        """Check if another tool call is allowed this turn.

        Returns:
            True if tool calls are allowed.
        """
        return self.tool_calls_this_turn < settings.max_tool_calls_per_turn

    def get_progress_summary(self) -> dict[str, Any]:
        """Get a summary of progress.

        Returns:
            Dictionary with progress information.
        """
        return {
            "turn_count": self.turn_count,
            "fields_resolved": len(self.fields_resolved),
            "fields_pending": len(self.fields_pending),
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "is_stuck": self.is_stuck(),
            "can_continue": self.can_continue(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "bioproject_id": self.bioproject_id,
            "local_metadata_paths": self.local_metadata_paths,
            "output_path": self.output_path,
            "fields_resolved": list(self.fields_resolved),
            "fields_pending": list(self.fields_pending),
            "retry_counts": self.retry_counts,
            "turn_count": self.turn_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "status": self.status.value,
            "termination_reason": self.termination_reason.value if self.termination_reason else None,
        }
