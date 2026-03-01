"""Tests for correction logging and confidence history."""

import pytest

from isaforge.session.database import get_session
from isaforge.session.manager import SessionManager
from isaforge.session.schemas import (
    Base,
    ConfidenceHistoryModel,
    CorrectionLogModel,
    FieldDecisionModel,
)


@pytest.fixture
async def session_manager(monkeypatch):
    """Create a session manager with in-memory database."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    
    # Create in-memory database for testing
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Patch the get_session function to use our test database
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def mock_get_session():
        async with test_session_maker() as session:
            yield session
            await session.commit()
    
    monkeypatch.setattr("isaforge.session.manager.get_session", mock_get_session)
    
    manager = SessionManager()
    
    yield manager
    
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_log_correction(session_manager):
    """Test logging a user correction."""
    # Create a session and field decision
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Original Title",
        confidence=0.8,
        justification="Inferred from metadata",
        source="llm",
    )
    
    # Log a correction
    correction_id = await session_manager.log_correction(
        field_decision_id=decision_id,
        original_value="Original Title",
        corrected_value="Corrected Title",
        correction_type="edit",
    )
    
    assert correction_id is not None
    
    # Verify correction was logged
    corrections = await session_manager.get_corrections(field_decision_id=decision_id)
    
    assert len(corrections) == 1
    assert corrections[0]["original_value"] == "Original Title"
    assert corrections[0]["corrected_value"] == "Corrected Title"
    assert corrections[0]["correction_type"] == "edit"


@pytest.mark.asyncio
async def test_get_corrections_by_session(session_manager):
    """Test retrieving corrections by session ID."""
    # Create session and multiple field decisions
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id1 = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Title 1",
        confidence=0.8,
        justification="Test",
        source="llm",
    )
    
    decision_id2 = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.description",
        value="Description 1",
        confidence=0.9,
        justification="Test",
        source="llm",
    )
    
    # Log corrections for both
    await session_manager.log_correction(
        field_decision_id=decision_id1,
        original_value="Title 1",
        corrected_value="Title 2",
        correction_type="edit",
    )
    
    await session_manager.log_correction(
        field_decision_id=decision_id2,
        original_value="Description 1",
        corrected_value="Description 2",
        correction_type="edit",
    )
    
    # Get all corrections for the session
    corrections = await session_manager.get_corrections(session_id=session.id)
    
    assert len(corrections) == 2


@pytest.mark.asyncio
async def test_correction_types(session_manager):
    """Test different correction types."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Original",
        confidence=0.8,
        justification="Test",
        source="llm",
    )
    
    # Test different correction types
    for correction_type in ["edit", "reject", "override"]:
        await session_manager.log_correction(
            field_decision_id=decision_id,
            original_value="Original",
            corrected_value=f"Corrected_{correction_type}",
            correction_type=correction_type,
        )
    
    corrections = await session_manager.get_corrections(field_decision_id=decision_id)
    
    assert len(corrections) == 3
    types = [c["correction_type"] for c in corrections]
    assert "edit" in types
    assert "reject" in types
    assert "override" in types


@pytest.mark.asyncio
async def test_save_confidence_history(session_manager):
    """Test saving confidence history snapshots."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Title",
        confidence=0.7,
        justification="Initial",
        source="llm",
    )
    
    # Save multiple confidence snapshots
    history_id1 = await session_manager.save_confidence_history(
        field_decision_id=decision_id,
        confidence=0.7,
        justification="Initial inference",
        source="llm",
    )
    
    history_id2 = await session_manager.save_confidence_history(
        field_decision_id=decision_id,
        confidence=0.85,
        justification="After additional context",
        source="llm",
    )
    
    history_id3 = await session_manager.save_confidence_history(
        field_decision_id=decision_id,
        confidence=0.95,
        justification="User confirmed",
        source="user",
    )
    
    assert history_id1 is not None
    assert history_id2 is not None
    assert history_id3 is not None
    
    # Retrieve history
    history = await session_manager.get_confidence_history(decision_id)
    
    assert len(history) == 3
    assert history[0]["confidence"] == 0.7
    assert history[1]["confidence"] == 0.85
    assert history[2]["confidence"] == 0.95


@pytest.mark.asyncio
async def test_confidence_history_timeline(session_manager):
    """Test that confidence history maintains chronological order."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Title",
        confidence=0.5,
        justification="Initial",
        source="llm",
    )
    
    # Save snapshots with increasing confidence
    confidences = [0.5, 0.6, 0.7, 0.8, 0.9]
    for conf in confidences:
        await session_manager.save_confidence_history(
            field_decision_id=decision_id,
            confidence=conf,
            justification=f"Confidence at {conf}",
            source="llm",
        )
    
    history = await session_manager.get_confidence_history(decision_id)
    
    assert len(history) == 5
    
    # Verify chronological order
    for i, record in enumerate(history):
        assert record["confidence"] == confidences[i]
    
    # Verify timestamps are in order
    timestamps = [record["timestamp"] for record in history]
    assert timestamps == sorted(timestamps)


@pytest.mark.asyncio
async def test_confidence_history_with_llm_call_id(session_manager):
    """Test tracking which LLM call produced each confidence score."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Title",
        confidence=0.8,
        justification="Test",
        source="llm",
        llm_call_id="call_123",
    )
    
    # Save history with LLM call ID
    await session_manager.save_confidence_history(
        field_decision_id=decision_id,
        confidence=0.8,
        justification="From LLM call",
        source="llm",
        llm_call_id="call_123",
    )
    
    history = await session_manager.get_confidence_history(decision_id)
    
    assert len(history) == 1
    assert history[0]["llm_call_id"] == "call_123"


@pytest.mark.asyncio
async def test_empty_corrections_and_history(session_manager):
    """Test querying when no corrections or history exist."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value="Title",
        confidence=0.8,
        justification="Test",
        source="llm",
    )
    
    # Query empty corrections
    corrections = await session_manager.get_corrections(field_decision_id=decision_id)
    assert len(corrections) == 0
    
    # Query empty history
    history = await session_manager.get_confidence_history(decision_id)
    assert len(history) == 0


@pytest.mark.asyncio
async def test_correction_with_null_values(session_manager):
    """Test logging corrections with null values."""
    session = await session_manager.create_session(bioproject_id="PRJNA123")
    
    decision_id = await session_manager.save_field_decision(
        session_id=session.id,
        field_path="investigation.title",
        value=None,
        confidence=0.5,
        justification="Unknown",
        source="llm",
    )
    
    # Log correction from null to value
    await session_manager.log_correction(
        field_decision_id=decision_id,
        original_value=None,
        corrected_value="New Value",
        correction_type="edit",
    )
    
    corrections = await session_manager.get_corrections(field_decision_id=decision_id)
    
    assert len(corrections) == 1
    assert corrections[0]["original_value"] is None
    assert corrections[0]["corrected_value"] == "New Value"
