"""Session manager for CRUD operations on sessions."""

import json
import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select

from isaforge.core.constants import MessageRole, SessionStatus, TerminationReason
from isaforge.core.exceptions import SessionNotFoundError
from isaforge.models.session import LLMCallRecord, Message, Session, ToolCallRecord
from isaforge.session.database import get_session
from isaforge.session.schemas import (
    ConfidenceHistoryModel,
    CorrectionLogModel,
    FieldDecisionModel,
    LLMCallModel,
    MessageModel,
    SessionModel,
    ToolCallModel,
)


class SessionManager:
    """Manager for session persistence operations."""

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())

    @staticmethod
    def _session_model_to_pydantic(model: SessionModel) -> Session:
        """Convert SQLAlchemy model to Pydantic model."""
        return Session(
            id=model.id,
            bioproject_id=model.bioproject_id,
            local_metadata_paths=json.loads(model.local_metadata_paths or "[]"),
            output_path=model.output_path,
            status=SessionStatus(model.status),
            termination_reason=(
                TerminationReason(model.termination_reason)
                if model.termination_reason
                else None
            ),
            created_at=model.created_at,
            updated_at=model.updated_at,
            turn_count=model.turn_count,
            total_tokens=model.total_tokens,
            total_llm_calls=model.total_llm_calls,
            fields_resolved=set(json.loads(model.fields_resolved or "[]")),
            fields_pending=set(json.loads(model.fields_pending or "[]")),
            retry_counts=json.loads(model.retry_counts or "{}"),
        )

    @staticmethod
    def _message_model_to_pydantic(model: MessageModel) -> Message:
        """Convert SQLAlchemy message model to Pydantic model."""
        return Message(
            id=model.id,
            role=MessageRole(model.role),
            content=model.content,
            timestamp=model.timestamp,
            tool_calls=json.loads(model.tool_calls) if model.tool_calls else None,
            tool_call_id=model.tool_call_id,
        )

    async def create_session(
        self,
        bioproject_id: str | None = None,
        local_metadata_paths: list[str] | None = None,
        output_path: str | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            bioproject_id: Optional BioProject ID.
            local_metadata_paths: Optional list of local metadata file paths.
            output_path: Optional output directory path.

        Returns:
            The created session.
        """
        session_id = self._generate_id()

        async with get_session() as db:
            model = SessionModel(
                id=session_id,
                bioproject_id=bioproject_id,
                local_metadata_paths=json.dumps(local_metadata_paths or []),
                output_path=output_path,
                status=SessionStatus.ACTIVE.value,
            )
            db.add(model)
            await db.flush()
            await db.refresh(model)
            return self._session_model_to_pydantic(model)

    async def get_session(self, session_id: str) -> Session:
        """Get a session by ID.

        Args:
            session_id: The session ID.

        Returns:
            The session.

        Raises:
            SessionNotFoundError: If the session doesn't exist.
        """
        async with get_session() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            return self._session_model_to_pydantic(model)

    async def update_session(self, session: Session) -> Session:
        """Update a session.

        Args:
            session: The session with updated values.

        Returns:
            The updated session.
        """
        async with get_session() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.id == session.id)
            )
            model = result.scalar_one_or_none()
            if model is None:
                raise SessionNotFoundError(f"Session not found: {session.id}")

            model.bioproject_id = session.bioproject_id
            model.local_metadata_paths = json.dumps(session.local_metadata_paths)
            model.output_path = session.output_path
            model.status = session.status.value
            model.termination_reason = (
                session.termination_reason.value if session.termination_reason else None
            )
            model.updated_at = datetime.utcnow()
            model.turn_count = session.turn_count
            model.total_tokens = session.total_tokens
            model.total_llm_calls = session.total_llm_calls
            model.fields_resolved = json.dumps(list(session.fields_resolved))
            model.fields_pending = json.dumps(list(session.fields_pending))
            model.retry_counts = json.dumps(session.retry_counts)

            await db.flush()
            await db.refresh(model)
            return self._session_model_to_pydantic(model)

    async def list_sessions(
        self,
        status: SessionStatus | None = None,
        limit: int = 50,
    ) -> list[Session]:
        """List sessions, optionally filtered by status.

        Args:
            status: Optional status filter.
            limit: Maximum number of sessions to return.

        Returns:
            List of sessions.
        """
        async with get_session() as db:
            query = select(SessionModel).order_by(SessionModel.created_at.desc())
            if status:
                query = query.where(SessionModel.status == status.value)
            query = query.limit(limit)

            result = await db.execute(query)
            models: Sequence[SessionModel] = result.scalars().all()
            return [self._session_model_to_pydantic(m) for m in models]

    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all related data.

        Args:
            session_id: The session ID to delete.
        """
        async with get_session() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            model = result.scalar_one_or_none()
            if model:
                await db.delete(model)

    async def save_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
    ) -> Message:
        """Save a message to a session.

        Args:
            session_id: The session ID.
            role: Message role.
            content: Message content.
            tool_calls: Optional tool calls.
            tool_call_id: Optional tool call ID this responds to.

        Returns:
            The saved message.
        """
        message_id = self._generate_id()

        async with get_session() as db:
            model = MessageModel(
                id=message_id,
                session_id=session_id,
                role=role.value,
                content=content,
                tool_calls=json.dumps(tool_calls) if tool_calls else None,
                tool_call_id=tool_call_id,
            )
            db.add(model)
            await db.flush()
            await db.refresh(model)
            return self._message_model_to_pydantic(model)

    async def get_conversation_history(self, session_id: str) -> list[Message]:
        """Get all messages for a session.

        Args:
            session_id: The session ID.

        Returns:
            List of messages in chronological order.
        """
        async with get_session() as db:
            result = await db.execute(
                select(MessageModel)
                .where(MessageModel.session_id == session_id)
                .order_by(MessageModel.timestamp)
            )
            models: Sequence[MessageModel] = result.scalars().all()
            return [self._message_model_to_pydantic(m) for m in models]

    async def save_llm_call(
        self,
        session_id: str,
        task: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: int = 0,
        tool_calls: list[str] | None = None,
        error: str | None = None,
    ) -> LLMCallRecord:
        """Save an LLM call record.

        Args:
            session_id: The session ID.
            task: Task being performed.
            model: Model used.
            prompt_tokens: Number of prompt tokens.
            completion_tokens: Number of completion tokens.
            latency_ms: Latency in milliseconds.
            tool_calls: Names of tools called.
            error: Error message if failed.

        Returns:
            The saved LLM call record.
        """
        call_id = self._generate_id()

        async with get_session() as db:
            db_model = LLMCallModel(
                id=call_id,
                session_id=session_id,
                task=task,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                tool_calls=json.dumps(tool_calls) if tool_calls else None,
                error=error,
            )
            db.add(db_model)
            await db.flush()

            return LLMCallRecord(
                id=call_id,
                session_id=session_id,
                task=task,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                tool_calls=tool_calls or [],
                error=error,
            )

    async def save_tool_call(
        self,
        llm_call_id: str,
        tool_name: str,
        arguments: dict,
        result: dict | None = None,
        duration_ms: int = 0,
        success: bool = True,
        error: str | None = None,
    ) -> ToolCallRecord:
        """Save a tool call record.

        Args:
            llm_call_id: The parent LLM call ID.
            tool_name: Name of the tool.
            arguments: Tool arguments.
            result: Tool result.
            duration_ms: Duration in milliseconds.
            success: Whether the call succeeded.
            error: Error message if failed.

        Returns:
            The saved tool call record.
        """
        call_id = self._generate_id()

        async with get_session() as db:
            db_model = ToolCallModel(
                id=call_id,
                llm_call_id=llm_call_id,
                tool_name=tool_name,
                arguments=json.dumps(arguments),
                result=json.dumps(result) if result else None,
                duration_ms=duration_ms,
                success=success,
                error=error,
            )
            db.add(db_model)
            await db.flush()

            return ToolCallRecord(
                id=call_id,
                llm_call_id=llm_call_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                duration_ms=duration_ms,
                success=success,
                error=error,
            )

    async def save_field_decision(
        self,
        session_id: str,
        field_path: str,
        value: str | None,
        confidence: float,
        justification: str,
        source: str,
        user_action: str = "pending",
        llm_call_id: str | None = None,
        alternatives: list[str] | None = None,
    ) -> str:
        """Save a field decision with auto-correction detection.

        Args:
            session_id: The session ID.
            field_path: Path to the field.
            value: Field value.
            confidence: Confidence score.
            justification: Explanation for the confidence.
            source: Source of the value.
            user_action: User action on this field.
            llm_call_id: ID of the LLM call that generated this.
            alternatives: Alternative values considered.

        Returns:
            The decision ID.
        """
        decision_id = self._generate_id()

        async with get_session() as db:
            # Check for existing decision for this field
            existing_result = await db.execute(
                select(FieldDecisionModel)
                .where(FieldDecisionModel.session_id == session_id)
                .where(FieldDecisionModel.field_path == field_path)
                .order_by(FieldDecisionModel.created_at.desc())
                .limit(1)
            )
            existing = existing_result.scalar_one_or_none()

            # Auto-log correction if value changed
            if existing and existing.value != value:
                correction_type = self._determine_correction_type(source, existing.source)
                await self.log_correction(
                    field_decision_id=existing.id,
                    original_value=existing.value,
                    corrected_value=value,
                    correction_type=correction_type,
                    reason=f"Value updated from {existing.source} to {source}",
                )

            # Save new decision
            db_model = FieldDecisionModel(
                id=decision_id,
                session_id=session_id,
                field_path=field_path,
                value=value,
                confidence=confidence,
                justification=justification,
                source=source,
                user_action=user_action,
                llm_call_id=llm_call_id,
                alternatives=json.dumps(alternatives) if alternatives else None,
            )
            db.add(db_model)
            await db.flush()

            return decision_id

    def _determine_correction_type(self, new_source: str, old_source: str) -> str:
        """Determine the type of correction based on sources.

        Args:
            new_source: Source of the new value.
            old_source: Source of the old value.

        Returns:
            Correction type string.
        """
        if "user" in new_source.lower():
            return "user_override"
        elif "llm" in new_source.lower() and "llm" in old_source.lower():
            return "llm_refinement"
        else:
            return "value_update"

    async def get_field_decisions(
        self, session_id: str
    ) -> list[dict]:
        """Get all field decisions for a session.

        Args:
            session_id: The session ID.

        Returns:
            List of field decisions as dictionaries.
        """
        async with get_session() as db:
            result = await db.execute(
                select(FieldDecisionModel)
                .where(FieldDecisionModel.session_id == session_id)
                .order_by(FieldDecisionModel.created_at)
            )
            models: Sequence[FieldDecisionModel] = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "field_path": m.field_path,
                    "value": m.value,
                    "confidence": m.confidence,
                    "justification": m.justification,
                    "source": m.source,
                    "user_action": m.user_action,
                    "llm_call_id": m.llm_call_id,
                    "alternatives": json.loads(m.alternatives) if m.alternatives else [],
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat(),
                }
                for m in models
            ]

    async def log_correction(
        self,
        field_decision_id: str,
        original_value: str | None,
        corrected_value: str | None,
        correction_type: str = "edit",
    ) -> str:
        """Log a user correction to a field value.

        Args:
            field_decision_id: The field decision being corrected.
            original_value: The original value before correction.
            corrected_value: The new corrected value.
            correction_type: Type of correction (edit, reject, override).

        Returns:
            The correction log ID.
        """
        correction_id = self._generate_id()

        async with get_session() as db:
            db_model = CorrectionLogModel(
                id=correction_id,
                field_decision_id=field_decision_id,
                original_value=original_value,
                corrected_value=corrected_value,
                correction_type=correction_type,
            )
            db.add(db_model)
            await db.flush()

            return correction_id

    async def get_corrections(
        self, session_id: str | None = None, field_decision_id: str | None = None
    ) -> list[dict]:
        """Get correction logs.

        Args:
            session_id: Optional session ID to filter by.
            field_decision_id: Optional field decision ID to filter by.

        Returns:
            List of correction logs as dictionaries.
        """
        async with get_session() as db:
            if field_decision_id:
                result = await db.execute(
                    select(CorrectionLogModel)
                    .where(CorrectionLogModel.field_decision_id == field_decision_id)
                    .order_by(CorrectionLogModel.timestamp)
                )
            elif session_id:
                result = await db.execute(
                    select(CorrectionLogModel)
                    .join(FieldDecisionModel)
                    .where(FieldDecisionModel.session_id == session_id)
                    .order_by(CorrectionLogModel.timestamp)
                )
            else:
                result = await db.execute(
                    select(CorrectionLogModel).order_by(CorrectionLogModel.timestamp)
                )

            models: Sequence[CorrectionLogModel] = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "field_decision_id": m.field_decision_id,
                    "original_value": m.original_value,
                    "corrected_value": m.corrected_value,
                    "correction_type": m.correction_type,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in models
            ]

    async def save_confidence_history(
        self,
        field_decision_id: str,
        confidence: float,
        justification: str | None = None,
        source: str | None = None,
        llm_call_id: str | None = None,
    ) -> str:
        """Save a confidence history snapshot.

        Args:
            field_decision_id: The field decision ID.
            confidence: The confidence score at this point.
            justification: Optional justification.
            source: Optional source of the confidence.
            llm_call_id: Optional LLM call that produced this.

        Returns:
            The history record ID.
        """
        history_id = self._generate_id()

        async with get_session() as db:
            db_model = ConfidenceHistoryModel(
                id=history_id,
                field_decision_id=field_decision_id,
                confidence=confidence,
                justification=justification,
                source=source,
                llm_call_id=llm_call_id,
            )
            db.add(db_model)
            await db.flush()

            return history_id

    async def get_confidence_history(
        self, field_decision_id: str
    ) -> list[dict]:
        """Get confidence history for a field decision.

        Args:
            field_decision_id: The field decision ID.

        Returns:
            List of confidence history records as dictionaries.
        """
        async with get_session() as db:
            result = await db.execute(
                select(ConfidenceHistoryModel)
                .where(ConfidenceHistoryModel.field_decision_id == field_decision_id)
                .order_by(ConfidenceHistoryModel.timestamp)
            )
            models: Sequence[ConfidenceHistoryModel] = result.scalars().all()
            return [
                {
                    "id": m.id,
                    "field_decision_id": m.field_decision_id,
                    "confidence": m.confidence,
                    "justification": m.justification,
                    "source": m.source,
                    "llm_call_id": m.llm_call_id,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in models
            ]

    async def get_session_messages(self, session_id: str) -> list[dict]:
        """Get all messages for a session in chronological order.

        Args:
            session_id: The session ID.

        Returns:
            List of message dictionaries.
        """
        async with get_session() as db:
            result = await db.execute(
                select(MessageModel)
                .where(MessageModel.session_id == session_id)
                .order_by(MessageModel.timestamp)
            )
            messages: Sequence[MessageModel] = result.scalars().all()
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in messages
            ]


# Global session manager instance
session_manager = SessionManager()
