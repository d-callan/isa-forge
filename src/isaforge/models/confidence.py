"""Confidence score models for tracking field-level decisions."""

from datetime import datetime

from pydantic import BaseModel, Field

from isaforge.core.constants import FieldSource, UserAction


class FieldConfidence(BaseModel):
    """Confidence information for a single field."""

    field_path: str = Field(..., description="Path to the field (e.g., 'study.title')")
    value: str | None = Field(default=None, description="Current field value")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    justification: str = Field(..., description="Explanation for the confidence score")
    source: FieldSource = Field(..., description="Source of the field value")
    user_action: UserAction = Field(
        default=UserAction.PENDING, description="User action on this field"
    )
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative values considered"
    )
    llm_call_id: str | None = Field(
        default=None, description="ID of the LLM call that generated this"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this was last updated"
    )


class ConfidenceSummary(BaseModel):
    """Summary of confidence scores for an ISA-Tab generation session."""

    session_id: str = Field(..., description="Session ID")
    total_fields: int = Field(default=0, description="Total number of fields")
    auto_accepted: int = Field(default=0, description="Fields auto-accepted (high confidence)")
    user_confirmed: int = Field(default=0, description="Fields confirmed by user")
    user_edited: int = Field(default=0, description="Fields edited by user")
    flagged: int = Field(default=0, description="Fields flagged for later review")
    pending: int = Field(default=0, description="Fields still pending")

    average_confidence: float = Field(
        default=0.0, description="Average confidence across all fields"
    )
    min_confidence: float = Field(
        default=1.0, description="Minimum confidence score"
    )
    max_confidence: float = Field(
        default=0.0, description="Maximum confidence score"
    )

    fields: dict[str, FieldConfidence] = Field(
        default_factory=dict, description="Per-field confidence information"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When this summary was created"
    )

    def update_stats(self) -> None:
        """Recalculate summary statistics from fields."""
        if not self.fields:
            return

        self.total_fields = len(self.fields)
        self.auto_accepted = sum(
            1 for f in self.fields.values() if f.user_action == UserAction.AUTO_ACCEPTED
        )
        self.user_confirmed = sum(
            1 for f in self.fields.values() if f.user_action == UserAction.USER_CONFIRMED
        )
        self.user_edited = sum(
            1 for f in self.fields.values() if f.user_action == UserAction.USER_EDITED
        )
        self.flagged = sum(
            1 for f in self.fields.values() if f.user_action == UserAction.FLAGGED
        )
        self.pending = sum(
            1 for f in self.fields.values() if f.user_action == UserAction.PENDING
        )

        confidences = [f.confidence for f in self.fields.values()]
        self.average_confidence = sum(confidences) / len(confidences)
        self.min_confidence = min(confidences)
        self.max_confidence = max(confidences)
