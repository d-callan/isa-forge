"""Unit tests for core modules (constants, exceptions)."""

import pytest

from isaforge.core.constants import (
    CONFIDENCE_SUMMARY_FILE,
    CHAT_LOG_FILE,
    DATA_DICTIONARY_FILE,
    PROVENANCE_FILE,
    FieldSource,
    MessageRole,
    SessionStatus,
    TerminationReason,
    UserAction,
)
from isaforge.core.exceptions import (
    CircuitBreakerOpenError,
    ISAForgeError,
    RetrievalError,
    OntologyMappingError,
    SessionNotFoundError,
    ISAValidationError,
)


class TestConstants:
    """Test core constants."""

    def test_file_constants(self):
        """Test file name constants."""
        assert CONFIDENCE_SUMMARY_FILE == "confidence_summary.json"
        assert CHAT_LOG_FILE == "chat_log.md"
        assert DATA_DICTIONARY_FILE == "data_dictionary.json"
        assert PROVENANCE_FILE == "provenance.json"

    def test_field_source_enum(self):
        """Test FieldSource enum values."""
        assert FieldSource.API_DATA.value == "api_data"
        assert FieldSource.LOCAL_FILE.value == "local_file"
        assert FieldSource.LLM_INFERENCE.value == "llm_inference"
        assert FieldSource.USER_INPUT.value == "user_input"

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.TOOL.value == "tool"

    def test_session_status_enum(self):
        """Test SessionStatus enum values."""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.FAILED.value == "failed"
        assert SessionStatus.ABANDONED.value == "abandoned"

    def test_termination_reason_enum(self):
        """Test TerminationReason enum values."""
        assert TerminationReason.SUCCESS.value == "success"
        assert TerminationReason.USER_EXIT.value == "user_exit"
        assert TerminationReason.ERROR.value == "error"
        assert TerminationReason.MAX_TURNS_EXCEEDED.value == "max_turns_exceeded"

    def test_user_action_enum(self):
        """Test UserAction enum values."""
        assert UserAction.AUTO_ACCEPTED.value == "auto_accepted"
        assert UserAction.USER_CONFIRMED.value == "user_confirmed"
        assert UserAction.USER_EDITED.value == "user_edited"
        assert UserAction.FLAGGED.value == "flagged"
        assert UserAction.PENDING.value == "pending"


class TestExceptions:
    """Test custom exceptions."""

    def test_isaforge_error(self):
        """Test base ISAForgeError."""
        error = ISAForgeError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_retrieval_error(self):
        """Test RetrievalError."""
        error = RetrievalError("Failed to fetch metadata")
        assert str(error) == "Failed to fetch metadata"
        assert isinstance(error, ISAForgeError)

    def test_ontology_mapping_error(self):
        """Test OntologyMappingError."""
        error = OntologyMappingError("Failed to map term")
        assert str(error) == "Failed to map term"
        assert isinstance(error, ISAForgeError)

    def test_session_not_found_error(self):
        """Test SessionNotFoundError."""
        error = SessionNotFoundError("Session not found")
        assert str(error) == "Session not found"
        assert isinstance(error, ISAForgeError)

    def test_isa_validation_error(self):
        """Test ISAValidationError."""
        error = ISAValidationError("Invalid field value")
        assert str(error) == "Invalid field value"
        assert isinstance(error, ISAForgeError)

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError."""
        error = CircuitBreakerOpenError("Circuit is open")
        assert str(error) == "Circuit is open"
        assert isinstance(error, ISAForgeError)

    def test_exception_inheritance(self):
        """Test exception inheritance chain."""
        # All custom exceptions should inherit from ISAForgeError
        assert issubclass(RetrievalError, ISAForgeError)
        assert issubclass(OntologyMappingError, ISAForgeError)
        assert issubclass(SessionNotFoundError, ISAForgeError)
        assert issubclass(ISAValidationError, ISAForgeError)
        assert issubclass(CircuitBreakerOpenError, ISAForgeError)

    def test_exception_can_be_raised(self):
        """Test exceptions can be raised and caught."""
        with pytest.raises(ISAForgeError):
            raise ISAForgeError("test")

        with pytest.raises(RetrievalError):
            raise RetrievalError("test")

        with pytest.raises(SessionNotFoundError):
            raise SessionNotFoundError("test")
