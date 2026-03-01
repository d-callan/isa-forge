"""Session and conversation state models."""

from datetime import datetime

from pydantic import BaseModel, Field

from isaforge.core.constants import MessageRole, SessionStatus, TerminationReason


class Message(BaseModel):
    """A message in the conversation."""

    id: str = Field(..., description="Unique message ID")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the message was sent"
    )
    tool_calls: list[dict] | None = Field(
        default=None, description="Tool calls made in this message"
    )
    tool_call_id: str | None = Field(
        default=None, description="ID of the tool call this message responds to"
    )


class LLMCallRecord(BaseModel):
    """Record of an LLM API call."""

    id: str = Field(..., description="Unique call ID")
    session_id: str = Field(..., description="Parent session ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the call was made"
    )
    task: str = Field(..., description="Task being performed (e.g., 'parse_metadata')")
    model: str = Field(..., description="Model used")
    prompt_tokens: int = Field(default=0, description="Number of prompt tokens")
    completion_tokens: int = Field(default=0, description="Number of completion tokens")
    latency_ms: int = Field(default=0, description="Latency in milliseconds")
    tool_calls: list[str] = Field(
        default_factory=list, description="Names of tools called"
    )
    error: str | None = Field(default=None, description="Error message if failed")


class ToolCallRecord(BaseModel):
    """Record of a tool call."""

    id: str = Field(..., description="Unique tool call ID")
    llm_call_id: str = Field(..., description="Parent LLM call ID")
    tool_name: str = Field(..., description="Name of the tool")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")
    result: dict | None = Field(default=None, description="Tool result")
    duration_ms: int = Field(default=0, description="Duration in milliseconds")
    success: bool = Field(default=True, description="Whether the call succeeded")
    error: str | None = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the call was made"
    )


class Session(BaseModel):
    """A generation session."""

    id: str = Field(..., description="Unique session ID")
    bioproject_id: str | None = Field(
        default=None, description="BioProject ID if applicable"
    )
    local_metadata_paths: list[str] = Field(
        default_factory=list, description="Paths to local metadata files"
    )
    output_path: str | None = Field(default=None, description="Output directory path")

    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE, description="Session status"
    )
    termination_reason: TerminationReason | None = Field(
        default=None, description="Reason for termination if completed"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the session was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the session was last updated"
    )

    turn_count: int = Field(default=0, description="Number of conversation turns")
    total_tokens: int = Field(default=0, description="Total tokens used")
    total_llm_calls: int = Field(default=0, description="Total LLM calls made")

    fields_resolved: set[str] = Field(
        default_factory=set, description="Set of resolved field paths"
    )
    fields_pending: set[str] = Field(
        default_factory=set, description="Set of pending field paths"
    )
    retry_counts: dict[str, int] = Field(
        default_factory=dict, description="Retry count per field"
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
