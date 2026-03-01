"""Unit tests for confidence models and scoring."""

from datetime import datetime

from isaforge.models.confidence import FieldConfidence, ConfidenceSummary
from isaforge.core.constants import FieldSource, UserAction


class TestFieldConfidence:
    """Test FieldConfidence model."""

    def test_creation(self):
        """Test creating a FieldConfidence."""
        fc = FieldConfidence(
            field_path="study.title",
            value="Test Study",
            confidence=0.95,
            justification="From BioProject metadata",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )

        assert fc.field_path == "study.title"
        assert fc.value == "Test Study"
        assert fc.confidence == 0.95
        assert fc.source == FieldSource.API_DATA

    def test_defaults(self):
        """Test default values."""
        fc = FieldConfidence(
            field_path="study.title",
            value="Test",
            confidence=0.5,
            justification="test",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.PENDING,
        )

        assert fc.alternatives == []
        assert fc.created_at is not None
        assert fc.updated_at is not None

    def test_with_alternatives(self):
        """Test with alternative values."""
        fc = FieldConfidence(
            field_path="study.organism",
            value="Homo sapiens",
            confidence=0.85,
            justification="Inferred from samples",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.PENDING,
            alternatives=["Mus musculus", "Rattus norvegicus"],
        )

        assert len(fc.alternatives) == 2
        assert "Mus musculus" in fc.alternatives


class TestConfidenceSummary:
    """Test ConfidenceSummary model."""

    def test_creation(self):
        """Test creating a ConfidenceSummary."""
        summary = ConfidenceSummary(session_id="test-session")

        assert summary.session_id == "test-session"
        assert summary.total_fields == 0
        assert summary.fields == {}

    def test_add_field(self):
        """Test adding fields to summary."""
        summary = ConfidenceSummary(session_id="test-session")

        summary.fields["study.title"] = FieldConfidence(
            field_path="study.title",
            value="Test Study",
            confidence=0.95,
            justification="From API",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )

        assert len(summary.fields) == 1
        assert "study.title" in summary.fields

    def test_update_stats(self):
        """Test updating statistics."""
        summary = ConfidenceSummary(session_id="test-session")

        summary.fields["field1"] = FieldConfidence(
            field_path="field1",
            value="value1",
            confidence=0.9,
            justification="test",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )
        summary.fields["field2"] = FieldConfidence(
            field_path="field2",
            value="value2",
            confidence=0.8,
            justification="test",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.USER_CONFIRMED,
        )
        summary.fields["field3"] = FieldConfidence(
            field_path="field3",
            value="value3",
            confidence=0.7,
            justification="test",
            source=FieldSource.USER_INPUT,
            user_action=UserAction.USER_EDITED,
        )

        summary.update_stats()

        assert summary.total_fields == 3
        assert summary.auto_accepted == 1
        assert summary.user_confirmed == 1
        assert summary.user_edited == 1
        assert summary.average_confidence == (0.9 + 0.8 + 0.7) / 3
        assert summary.min_confidence == 0.7
        assert summary.max_confidence == 0.9

    def test_update_stats_empty(self):
        """Test updating stats with no fields."""
        summary = ConfidenceSummary(session_id="test-session")
        summary.update_stats()

        assert summary.total_fields == 0
        assert summary.average_confidence == 0.0

    def test_flagged_and_pending(self):
        """Test flagged and pending field counts."""
        summary = ConfidenceSummary(session_id="test-session")

        summary.fields["flagged_field"] = FieldConfidence(
            field_path="flagged_field",
            value="needs review",
            confidence=0.3,
            justification="low confidence",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.FLAGGED,
        )
        summary.fields["pending_field"] = FieldConfidence(
            field_path="pending_field",
            value="pending",
            confidence=0.5,
            justification="awaiting confirmation",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.PENDING,
        )

        summary.update_stats()

        assert summary.flagged == 1
        assert summary.pending == 1
