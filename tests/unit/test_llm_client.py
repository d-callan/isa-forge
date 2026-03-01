"""Tests for LLM client implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from isaforge.agents.llm import get_llm_client
from isaforge.agents.llm.base import LLMClient, LLMMessage, LLMResponse, MessageRole


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""

    def __init__(self, model: str = "mock-model", session_id: str | None = None):
        super().__init__(model=model, session_id=session_id)
        self.call_count = 0

    async def _call(self, messages, tools=None, temperature=0.0, max_tokens=4096):
        self.call_count += 1
        return LLMResponse(
            content="Mock response",
            prompt_tokens=10,
            completion_tokens=20,
            model=self.model,
        )

    def get_provider_name(self) -> str:
        return "mock"


@pytest.mark.asyncio
async def test_llm_client_chat():
    """Test basic chat functionality."""
    client = MockLLMClient()

    messages = [
        LLMMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        LLMMessage(role=MessageRole.USER, content="Hello!"),
    ]

    response, record = await client.chat(messages=messages, task="test_chat")

    assert response.content == "Mock response"
    assert response.prompt_tokens == 10
    assert response.completion_tokens == 20
    assert response.total_tokens == 30

    assert record.task == "test_chat"
    assert record.model == "mock-model"
    assert record.prompt_tokens == 10
    assert record.completion_tokens == 20
    assert record.system_prompt_hash is not None
    assert record.user_prompt_hash is not None


@pytest.mark.asyncio
async def test_llm_client_prompt_hashing():
    """Test that prompt hashes are computed correctly."""
    client = MockLLMClient()

    system_content = "You are a helpful assistant."
    user_content = "Hello!"

    messages = [
        LLMMessage(role=MessageRole.SYSTEM, content=system_content),
        LLMMessage(role=MessageRole.USER, content=user_content),
    ]

    _, record1 = await client.chat(messages=messages)
    _, record2 = await client.chat(messages=messages)

    # Same content should produce same hashes
    assert record1.system_prompt_hash == record2.system_prompt_hash
    assert record1.user_prompt_hash == record2.user_prompt_hash

    # Different content should produce different hashes
    different_messages = [
        LLMMessage(role=MessageRole.SYSTEM, content="Different system prompt"),
        LLMMessage(role=MessageRole.USER, content=user_content),
    ]

    _, record3 = await client.chat(messages=different_messages)
    assert record3.system_prompt_hash != record1.system_prompt_hash
    assert record3.user_prompt_hash == record1.user_prompt_hash


@pytest.mark.asyncio
async def test_llm_client_with_session_id():
    """Test client with session ID for metrics tracking."""
    session_id = "test-session-123"
    client = MockLLMClient(session_id=session_id)

    messages = [LLMMessage(role=MessageRole.USER, content="Test")]

    _, record = await client.chat(messages=messages)

    assert record.session_id == session_id


@pytest.mark.asyncio
async def test_llm_message_to_dict():
    """Test LLMMessage serialization."""
    msg = LLMMessage(role=MessageRole.USER, content="Hello")
    msg_dict = msg.to_dict()

    assert msg_dict["role"] == "user"
    assert msg_dict["content"] == "Hello"
    assert "tool_call_id" not in msg_dict

    msg_with_tool = LLMMessage(
        role=MessageRole.TOOL, content="Result", tool_call_id="call_123"
    )
    tool_dict = msg_with_tool.to_dict()

    assert tool_dict["tool_call_id"] == "call_123"


def test_llm_response_properties():
    """Test LLMResponse computed properties."""
    response = LLMResponse(
        content="Test",
        prompt_tokens=100,
        completion_tokens=50,
        model="test-model",
    )

    assert response.total_tokens == 150
    assert not response.has_tool_calls

    from isaforge.agents.llm.base import LLMToolCall

    response_with_tools = LLMResponse(
        content=None,
        tool_calls=[
            LLMToolCall(id="call_1", name="test_tool", arguments={"arg": "value"})
        ],
        prompt_tokens=100,
        completion_tokens=50,
        model="test-model",
    )

    assert response_with_tools.has_tool_calls
    assert len(response_with_tools.tool_calls) == 1


def test_get_llm_client_anthropic():
    """Test getting Anthropic client from factory."""
    with patch("isaforge.agents.llm.settings") as mock_settings:
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_model = "claude-3-5-sonnet-20241022"
        mock_settings.anthropic_api_key = "test-key"

        with patch("isaforge.agents.llm.anthropic.AnthropicClient") as MockClient:
            get_llm_client(session_id="test-session")
            MockClient.assert_called_once_with(session_id="test-session")


def test_get_llm_client_google():
    """Test getting Google client from factory."""
    with patch("isaforge.agents.llm.settings") as mock_settings:
        mock_settings.llm_provider = "google"
        mock_settings.google_api_key = "test-key"

        with patch("isaforge.agents.llm.google.GoogleClient") as MockClient:
            get_llm_client(session_id="test-session")
            MockClient.assert_called_once_with(session_id="test-session")


def test_get_llm_client_ollama():
    """Test getting Ollama client from factory."""
    with patch("isaforge.agents.llm.settings") as mock_settings:
        mock_settings.llm_provider = "ollama"
        mock_settings.ollama_base_url = "http://localhost:11434"

        with patch("isaforge.agents.llm.ollama.OllamaClient") as MockClient:
            get_llm_client(session_id="test-session")
            MockClient.assert_called_once_with(session_id="test-session")


def test_get_llm_client_unsupported():
    """Test error for unsupported provider."""
    with patch("isaforge.agents.llm.settings") as mock_settings:
        mock_settings.llm_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            get_llm_client()


@pytest.mark.asyncio
async def test_llm_client_error_handling():
    """Test error handling in LLM client."""

    class ErrorClient(LLMClient):
        async def _call(self, messages, tools=None, temperature=0.0, max_tokens=4096):
            raise RuntimeError("API Error")

        def get_provider_name(self) -> str:
            return "error"

    client = ErrorClient(model="error-model")
    messages = [LLMMessage(role=MessageRole.USER, content="Test")]

    with pytest.raises(RuntimeError, match="API Error"):
        await client.chat(messages=messages)
