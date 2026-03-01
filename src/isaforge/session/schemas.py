"""SQLAlchemy ORM models for session persistence."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class SessionModel(Base):
    """SQLAlchemy model for sessions."""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    bioproject_id = Column(String(50), nullable=True, index=True)
    local_metadata_paths = Column(Text, nullable=True)  # JSON array
    output_path = Column(String(500), nullable=True)

    status = Column(String(20), default="active", index=True)
    termination_reason = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    turn_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_llm_calls = Column(Integer, default=0)

    fields_resolved = Column(Text, nullable=True)  # JSON array
    fields_pending = Column(Text, nullable=True)  # JSON array
    retry_counts = Column(Text, nullable=True)  # JSON object

    # Relationships
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan")
    llm_calls = relationship("LLMCallModel", back_populates="session", cascade="all, delete-orphan")
    field_decisions = relationship(
        "FieldDecisionModel", back_populates="session", cascade="all, delete-orphan"
    )


class MessageModel(Base):
    """SQLAlchemy model for conversation messages."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    tool_calls = Column(Text, nullable=True)  # JSON array
    tool_call_id = Column(String(50), nullable=True)

    # Relationships
    session = relationship("SessionModel", back_populates="messages")


class LLMCallModel(Base):
    """SQLAlchemy model for LLM call records."""

    __tablename__ = "llm_calls"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    task = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    tool_calls = Column(Text, nullable=True)  # JSON array
    error = Column(Text, nullable=True)

    # Prompt tracking (hash-based versioning)
    system_prompt_hash = Column(String(64), nullable=True, index=True)
    user_prompt_hash = Column(String(64), nullable=True, index=True)

    # Relationships
    session = relationship("SessionModel", back_populates="llm_calls")
    tool_call_records = relationship(
        "ToolCallModel", back_populates="llm_call", cascade="all, delete-orphan"
    )


class ToolCallModel(Base):
    """SQLAlchemy model for tool call records."""

    __tablename__ = "tool_calls"

    id = Column(String(36), primary_key=True)
    llm_call_id = Column(String(36), ForeignKey("llm_calls.id"), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    arguments = Column(Text, nullable=True)  # JSON object
    result = Column(Text, nullable=True)  # JSON object
    duration_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    llm_call = relationship("LLMCallModel", back_populates="tool_call_records")


class FieldDecisionModel(Base):
    """SQLAlchemy model for field decisions."""

    __tablename__ = "field_decisions"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    field_path = Column(String(200), nullable=False, index=True)
    value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False)
    justification = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    user_action = Column(String(20), default="pending")
    llm_call_id = Column(String(36), nullable=True)
    alternatives = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("SessionModel", back_populates="field_decisions")
    confidence_history = relationship(
        "ConfidenceHistoryModel", back_populates="field_decision", cascade="all, delete-orphan"
    )
    corrections = relationship(
        "CorrectionLogModel", back_populates="field_decision", cascade="all, delete-orphan"
    )


class PromptVersionModel(Base):
    """SQLAlchemy model for tracking prompt versions via content hash."""

    __tablename__ = "prompt_versions"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CorrectionLogModel(Base):
    """SQLAlchemy model for tracking user corrections to field values."""

    __tablename__ = "correction_logs"

    id = Column(String(36), primary_key=True)
    field_decision_id = Column(
        String(36), ForeignKey("field_decisions.id"), nullable=False, index=True
    )
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    correction_type = Column(String(20), nullable=False)  # edit, reject, override
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    field_decision = relationship("FieldDecisionModel", back_populates="corrections")


class ConfidenceHistoryModel(Base):
    """SQLAlchemy model for tracking confidence score changes over time."""

    __tablename__ = "confidence_history"

    id = Column(String(36), primary_key=True)
    field_decision_id = Column(
        String(36), ForeignKey("field_decisions.id"), nullable=False, index=True
    )
    confidence = Column(Float, nullable=False)
    justification = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    llm_call_id = Column(String(36), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    field_decision = relationship("FieldDecisionModel", back_populates="confidence_history")
