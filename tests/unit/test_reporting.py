"""Unit tests for reporting modules."""

import json
from datetime import datetime

from isaforge.reporting.confidence_summary import generate_confidence_summary, load_confidence_summary
from isaforge.reporting.provenance import generate_provenance, load_provenance, ProvenanceRecord
from isaforge.reporting.data_dictionary import generate_data_dictionary, load_data_dictionary
from isaforge.reporting.chat_log import generate_chat_log
from isaforge.models.confidence import FieldConfidence, ConfidenceSummary
from isaforge.models.session import Message
from isaforge.core.constants import FieldSource, UserAction, MessageRole


class TestConfidenceSummary:
    """Test confidence summary generation."""

    def test_generate_confidence_summary(self, temp_dir):
        """Test generating confidence summary JSON."""
        summary = ConfidenceSummary(session_id="test-session")
        summary.fields["study.title"] = FieldConfidence(
            field_path="study.title",
            value="Test Study",
            confidence=0.95,
            justification="From BioProject metadata",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )
        summary.update_stats()

        output_path = generate_confidence_summary(summary, temp_dir)

        assert output_path.exists()
        assert output_path.name == "confidence_summary.json"

        # Verify content
        content = json.loads(output_path.read_text())
        assert content["session_id"] == "test-session"
        assert "fields" in content

    def test_load_confidence_summary(self, temp_dir):
        """Test loading confidence summary from JSON."""
        # Create a summary file
        summary_data = {
            "session_id": "test-session",
            "summary": {"total_fields": 1},
            "fields": {}
        }
        summary_file = temp_dir / "confidence_summary.json"
        summary_file.write_text(json.dumps(summary_data))

        # load_confidence_summary expects a file path, not directory
        loaded = load_confidence_summary(summary_file)

        assert loaded is not None
        assert loaded["session_id"] == "test-session"


class TestProvenanceReport:
    """Test provenance report generation."""

    def test_generate_provenance(self, temp_dir):
        """Test generating provenance report."""
        record = ProvenanceRecord(
            session_id="test-session",
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
        )

        output_path = generate_provenance(record, temp_dir)

        assert output_path.exists()
        assert output_path.name == "provenance.json"

        content = json.loads(output_path.read_text())
        assert content["session_id"] == "test-session"

    def test_load_provenance(self, temp_dir):
        """Test loading provenance report."""
        provenance_data = {
            "session_id": "test-session",
            "created_at": datetime.utcnow().isoformat(),
            "llm": {"provider": "anthropic", "model": "claude-3-sonnet"},
            "data_sources": [],
            "field_provenance": {},
        }
        provenance_file = temp_dir / "provenance.json"
        provenance_file.write_text(json.dumps(provenance_data))

        loaded = load_provenance(provenance_file)

        assert loaded is not None
        assert loaded["session_id"] == "test-session"

    def test_generate_provenance_with_enhancements(self, temp_dir):
        """Test generating provenance with corrections and confidence history."""
        from isaforge.reporting.provenance import ConfidenceSnapshot, CorrectionInfo

        record = ProvenanceRecord(
            session_id="test-session",
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
            prompt_hashes_used=["hash1", "hash2"],
            corrections=[
                CorrectionInfo(
                    field_path="investigation.title",
                    original_value="Original",
                    corrected_value="Corrected",
                    correction_type="edit",
                )
            ],
            confidence_history={
                "investigation.title": [
                    ConfidenceSnapshot(confidence=0.7, justification="Initial"),
                    ConfidenceSnapshot(confidence=0.9, justification="Updated"),
                ]
            },
        )

        output_path = generate_provenance(record, temp_dir)

        assert output_path.exists()

        content = json.loads(output_path.read_text())
        assert "prompt_hashes_used" in content
        assert len(content["prompt_hashes_used"]) == 2
        assert "corrections" in content
        assert len(content["corrections"]) == 1
        assert content["corrections"][0]["field_path"] == "investigation.title"
        assert "confidence_history" in content
        assert "investigation.title" in content["confidence_history"]
        assert len(content["confidence_history"]["investigation.title"]) == 2
        assert "summary" in content
        assert content["summary"]["total_corrections"] == 1
        assert content["summary"]["unique_prompts"] == 2


class TestDataDictionary:
    """Test data dictionary generation."""

    def test_generate_data_dictionary(self, temp_dir):
        """Test generating data dictionary."""
        from isaforge.ontology.custom_terms import DataDictionary

        dictionary = DataDictionary(session_id="test-session")

        output_path = generate_data_dictionary(dictionary, temp_dir)

        assert output_path.exists()
        assert output_path.name == "data_dictionary.json"

    def test_load_data_dictionary(self, temp_dir):
        """Test loading data dictionary."""
        dict_data = {"terms": [], "version": "1.0"}
        dict_file = temp_dir / "data_dictionary.json"
        dict_file.write_text(json.dumps(dict_data))

        # load_data_dictionary expects file path
        loaded = load_data_dictionary(dict_file)

        assert loaded is not None


class TestChatLog:
    """Test chat log generation."""

    def test_generate_chat_log(self, temp_dir):
        """Test generating chat log markdown."""
        from isaforge.models.session import Message
        from isaforge.core.constants import MessageRole

        messages = [
            Message(id="1", role=MessageRole.USER, content="Generate ISA-Tab for PRJNA123456"),
            Message(id="2", role=MessageRole.ASSISTANT, content="I'll help you generate ISA-Tab metadata."),
        ]

        # generate_chat_log signature: (session_id, messages, output_dir, metadata)
        output_path = generate_chat_log(
            session_id="test-session",
            messages=messages,
            output_dir=temp_dir,
        )

        assert output_path.exists()
        assert output_path.name == "chat_log.md"

        content = output_path.read_text()
        assert "# ISA-Forge Chat Log" in content
        assert "test-session" in content

    def test_generate_chat_log_empty_messages(self, temp_dir):
        """Test chat log with no messages."""
        output_path = generate_chat_log(
            session_id="test-session",
            messages=[],
            output_dir=temp_dir,
        )

        assert output_path.exists()
        content = output_path.read_text()
        assert "# ISA-Forge Chat Log" in content


class TestReportingIntegration:
    """Test reporting modules working together."""

    def test_full_report_generation(self, temp_dir):
        """Test generating all reports for a session."""
        from isaforge.ontology.custom_terms import DataDictionary
        from isaforge.models.session import Message
        from isaforge.core.constants import MessageRole

        # Create confidence summary
        summary = ConfidenceSummary(session_id="test-session")
        summary.fields["study.title"] = FieldConfidence(
            field_path="study.title",
            value="Test Study",
            confidence=0.95,
            justification="From BioProject",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )
        summary.update_stats()

        # Create provenance
        provenance = ProvenanceRecord(
            session_id="test-session",
            llm_provider="anthropic",
            llm_model="claude-3-sonnet",
        )

        # Create data dictionary
        dictionary = DataDictionary(session_id="test-session")

        # Create messages
        messages = [
            Message(id="1", role=MessageRole.USER, content="Generate ISA-Tab"),
        ]

        # Generate all reports
        conf_path = generate_confidence_summary(summary, temp_dir)
        prov_path = generate_provenance(provenance, temp_dir)
        dict_path = generate_data_dictionary(dictionary, temp_dir)
        chat_path = generate_chat_log("test-session", messages, temp_dir)

        # Verify all files exist
        assert conf_path.exists()
        assert prov_path.exists()
        assert dict_path.exists()
        assert chat_path.exists()

        # Verify directory structure
        files = list(temp_dir.iterdir())
        assert len(files) == 4
