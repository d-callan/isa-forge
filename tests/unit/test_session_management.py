"""Unit tests for session management."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from isaforge.session.database import init_database
from isaforge.session.manager import SessionManager
from isaforge.session.schemas import SessionModel, MessageModel
from isaforge.core.constants import SessionStatus, MessageRole
from isaforge.models.session import Session, Message, LLMCallRecord


class TestSessionModels:
    """Test session Pydantic models."""

    def test_session_creation(self):
        """Test creating a Session model."""
        session = Session(
            id="test-session-123",
            status=SessionStatus.ACTIVE,
            bioproject_id="PRJNA123456",
        )

        assert session.id == "test-session-123"
        assert session.status == SessionStatus.ACTIVE
        assert session.bioproject_id == "PRJNA123456"

    def test_session_defaults(self):
        """Test Session default values."""
        session = Session(
            id="test-session",
            status=SessionStatus.ACTIVE,
        )

        assert session.bioproject_id is None
        assert session.turn_count == 0
        assert session.local_metadata_paths == []

    def test_message_creation(self):
        """Test creating a Message model."""
        msg = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello, world!",
        )

        assert msg.id == "msg-123"
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"
        assert msg.timestamp is not None

    def test_llm_call_record(self):
        """Test creating an LLMCallRecord."""
        record = LLMCallRecord(
            id="call-123",
            session_id="session-123",
            task="parse_metadata",
            model="claude-3-sonnet",
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert record.id == "call-123"
        assert record.task == "parse_metadata"
        assert record.prompt_tokens == 100


class TestSessionSchemas:
    """Test SQLAlchemy session schemas."""

    def test_session_model_table_name(self):
        """Test SessionModel table name."""
        assert SessionModel.__tablename__ == "sessions"

    def test_message_model_table_name(self):
        """Test MessageModel table name."""
        assert MessageModel.__tablename__ == "messages"


class TestSessionManager:
    """Test SessionManager helper methods."""

    def test_generate_id(self):
        """Test ID generation."""
        id1 = SessionManager._generate_id()
        id2 = SessionManager._generate_id()

        assert id1 != id2
        assert len(id1) == 36  # UUID format

    def test_session_model_to_pydantic(self):
        """Test converting SQLAlchemy model to Pydantic."""
        # Create a mock SessionModel
        mock_model = MagicMock()
        mock_model.id = "test-session"
        mock_model.bioproject_id = "PRJNA123456"
        mock_model.local_metadata_paths = "[]"
        mock_model.output_path = "/tmp/output"
        mock_model.status = "active"
        mock_model.termination_reason = None
        mock_model.created_at = datetime.utcnow()
        mock_model.updated_at = datetime.utcnow()
        mock_model.turn_count = 5
        mock_model.total_tokens = 1000
        mock_model.total_llm_calls = 3
        mock_model.fields_resolved = '["study.title"]'
        mock_model.fields_pending = '["study.organism"]'
        mock_model.retry_counts = "{}"

        session = SessionManager._session_model_to_pydantic(mock_model)

        assert session.id == "test-session"
        assert session.bioproject_id == "PRJNA123456"
        assert session.status == SessionStatus.ACTIVE
        assert session.turn_count == 5

    def test_message_model_to_pydantic(self):
        """Test converting message model to Pydantic."""
        mock_model = MagicMock()
        mock_model.id = "msg-123"
        mock_model.role = "user"
        mock_model.content = "Hello"
        mock_model.timestamp = datetime.utcnow()
        mock_model.tool_calls = None
        mock_model.tool_call_id = None

        message = SessionManager._message_model_to_pydantic(mock_model)

        assert message.id == "msg-123"
        assert message.role == MessageRole.USER
        assert message.content == "Hello"


class TestSessionDatabase:
    """Test database initialization."""

    @pytest.mark.asyncio
    async def test_init_database(self):
        """Test database initialization."""
        with patch('isaforge.session.database.create_async_engine') as mock_engine:
            mock_engine.return_value = MagicMock()

            # Should not raise
            await init_database()
