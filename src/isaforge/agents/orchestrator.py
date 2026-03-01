"""Main orchestrator agent for ISA-Tab generation."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from isaforge.agents.prompts.system import SYSTEM_PROMPT
from isaforge.agents.state import ConversationState
from isaforge.core.config import settings
from isaforge.core.constants import FieldSource, SessionStatus, TerminationReason, UserAction
from isaforge.core.exceptions import AgentError, AgentLoopError, AgentTimeoutError
from isaforge.models.confidence import ConfidenceSummary, FieldConfidence
from isaforge.observability.logger import get_logger
from isaforge.observability.metrics import MetricsCollector, Timer
from isaforge.session.manager import session_manager

logger = get_logger(__name__)


class FieldDecision(BaseModel):
    """A decision about a field value."""

    field_path: str = Field(..., description="Path to the field")
    value: Any = Field(..., description="The field value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    justification: str = Field(..., description="Explanation for the confidence")
    source: FieldSource = Field(..., description="Source of the value")
    alternatives: list[Any] = Field(default_factory=list, description="Alternative values")


class AgentResponse(BaseModel):
    """Response from the agent."""

    message: str = Field(..., description="Message to display to user")
    field_decisions: list[FieldDecision] = Field(
        default_factory=list, description="Field decisions made"
    )
    questions: list[str] = Field(
        default_factory=list, description="Questions for the user"
    )
    needs_user_input: bool = Field(
        default=False, description="Whether user input is needed"
    )
    is_complete: bool = Field(
        default=False, description="Whether generation is complete"
    )


class ISAForgeOrchestrator:
    """Orchestrator for ISA-Tab generation conversations."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.state: ConversationState | None = None
        self.confidence_summary: ConfidenceSummary | None = None
        self.metrics = None
        self.pydantic_agent = None
        self.message_history: list[dict] = []

    async def start_session(
        self,
        bioproject_id: str | None = None,
        local_metadata_paths: list[str] | None = None,
        output_path: str | None = None,
    ) -> str:
        """Start a new generation session.

        Args:
            bioproject_id: Optional BioProject accession.
            local_metadata_paths: Optional list of local file paths.
            output_path: Output directory path.

        Returns:
            Session ID.
        """
        # Create session in database
        session = await session_manager.create_session(
            bioproject_id=bioproject_id,
            local_metadata_paths=local_metadata_paths or [],
            output_path=output_path,
        )

        # Initialize state
        self.state = ConversationState(
            session_id=session.id,
            bioproject_id=bioproject_id,
            local_metadata_paths=local_metadata_paths or [],
            output_path=output_path,
        )

        # Initialize confidence summary
        self.confidence_summary = ConfidenceSummary(session_id=session.id)

        # Initialize metrics
        self.metrics = MetricsCollector.get_or_create(session.id)

        # Initialize Pydantic AI agent
        from isaforge.agents.pydantic_agent import ISAForgeAgent
        self.pydantic_agent = ISAForgeAgent(session_id=session.id)

        # Initialize empty message history
        self.message_history = []

        logger.info(
            "session_started",
            session_id=session.id,
            bioproject_id=bioproject_id,
            local_file_count=len(local_metadata_paths or []),
        )

        return session.id

    async def resume_session(self, session_id: str) -> None:
        """Resume an existing session.

        Args:
            session_id: The session ID to resume.
        """
        session = await session_manager.get_session(session_id)

        self.state = ConversationState(
            session_id=session.id,
            bioproject_id=session.bioproject_id,
            local_metadata_paths=session.local_metadata_paths,
            output_path=session.output_path,
            fields_resolved=session.fields_resolved,
            fields_pending=session.fields_pending,
            retry_counts=session.retry_counts,
            turn_count=session.turn_count,
            total_prompt_tokens=session.total_tokens,
            status=session.status,
        )

        self.confidence_summary = ConfidenceSummary(session_id=session.id)
        self.metrics = MetricsCollector.get_or_create(session.id)

        # Initialize Pydantic AI agent
        from isaforge.agents.pydantic_agent import ISAForgeAgent
        self.pydantic_agent = ISAForgeAgent(session_id=session_id)

        # Load message history
        self.message_history = await session_manager.get_session_messages(session_id)

        # Load existing field decisions
        decisions = await session_manager.get_field_decisions(session_id)
        for decision in decisions:
            self.confidence_summary.fields[decision["field_path"]] = FieldConfidence(
                field_path=decision["field_path"],
                value=decision["value"],
                confidence=decision["confidence"],
                justification=decision["justification"],
                source=FieldSource(decision["source"]),
                user_action=UserAction(decision["user_action"]),
            )

        logger.info(
            "session_resumed",
            session_id=session_id,
            turn_count=self.state.turn_count,
            fields_resolved=len(self.state.fields_resolved),
            message_count=len(self.message_history),
        )

    async def process_turn(self, user_message: str | None = None) -> AgentResponse:
        """Process a conversation turn.

        Args:
            user_message: Optional user message/input.

        Returns:
            Agent response with decisions and/or questions.

        Raises:
            AgentError: If processing fails.
        """
        if self.state is None:
            raise AgentError("No active session. Call start_session first.")

        self.state.start_turn()

        if user_message:
            self.state.record_user_input()
            await session_manager.save_message(
                self.state.session_id,
                role="user",
                content=user_message,
            )

        # Check termination conditions
        should_terminate, reason = self.state.should_terminate()
        if should_terminate:
            return await self._handle_termination(reason)

        with Timer("agent_turn", {"session_id": self.state.session_id}):
            try:
                # Determine what to do based on state
                if not self.state.metadata and self.state.bioproject_id:
                    # Need to fetch BioProject metadata
                    return await self._fetch_initial_metadata()

                if not self.state.metadata and self.state.local_metadata_paths:
                    # Need to parse local files
                    return await self._parse_local_files()

                if self.state.fields_pending:
                    # Process pending fields
                    return await self._process_pending_fields(user_message)

                # Generate ISA structure if we have metadata
                if self.state.metadata:
                    return await self._generate_isa_structure()

                # Nothing to do
                return AgentResponse(
                    message="No data sources provided. Please provide a BioProject ID or local metadata files.",
                    needs_user_input=True,
                )

            except Exception as e:
                logger.error("agent_turn_error", error=str(e))
                raise AgentError(f"Error processing turn: {e}") from e

    async def _fetch_initial_metadata(self) -> AgentResponse:
        """Fetch initial metadata from BioProject."""
        from isaforge.agents.tools.metadata_tools import (
            FetchBioProjectInput,
            fetch_bioproject_metadata,
        )

        self.state.record_tool_call()

        result = await fetch_bioproject_metadata(
            FetchBioProjectInput(bioproject_id=self.state.bioproject_id)
        )

        if not result.success:
            return AgentResponse(
                message=f"Failed to fetch BioProject metadata: {result.error}",
                needs_user_input=True,
                questions=["Would you like to try a different BioProject ID or provide local metadata files?"],
            )

        # Store metadata
        self.state.metadata = result.raw_data

        # Fetch linked publications if available
        if result.linked_pubmed_ids:
            from isaforge.agents.tools.metadata_tools import (
                FetchPublicationsInput,
                fetch_publications,
            )

            self.state.record_tool_call()
            pub_result = await fetch_publications(
                FetchPublicationsInput(
                    pmids=result.linked_pubmed_ids,
                    max_count=settings.max_publications,
                )
            )
            if pub_result.success:
                self.state.publications = [p.model_dump() for p in pub_result.publications]

        # Identify fields to populate
        self._identify_required_fields()

        # Build response
        summary = self._build_metadata_summary(result)

        return AgentResponse(
            message=summary,
            needs_user_input=False,
        )

    async def _parse_local_files(self) -> AgentResponse:
        """Parse local metadata files."""
        from isaforge.agents.tools.metadata_tools import (
            ParseLocalFileInput,
            parse_local_file,
        )

        all_data = {}
        errors = []

        for file_path in self.state.local_metadata_paths:
            self.state.record_tool_call()
            result = await parse_local_file(ParseLocalFileInput(file_path=file_path))

            if result.success:
                all_data[file_path] = {
                    "file_type": result.file_type,
                    "row_count": result.row_count,
                    "columns": result.columns,
                    "sample_data": result.sample_data,
                }
            else:
                errors.append(f"{file_path}: {result.error}")

        if errors and not all_data:
            return AgentResponse(
                message=f"Failed to parse files:\n" + "\n".join(errors),
                needs_user_input=True,
            )

        self.state.metadata = {"local_files": all_data}
        self._identify_required_fields()

        summary = f"Parsed {len(all_data)} file(s):\n"
        for path, data in all_data.items():
            summary += f"- {path}: {data['row_count']} rows, {len(data['columns'])} columns\n"

        if errors:
            summary += f"\nWarnings:\n" + "\n".join(errors)

        return AgentResponse(
            message=summary,
            needs_user_input=False,
        )

    async def _process_pending_fields(self, user_message: str | None) -> AgentResponse:
        """Process pending fields, potentially using user input."""
        decisions = []
        questions = []

        # Process up to 5 pending fields per turn
        fields_to_process = list(self.state.fields_pending)[:5]

        for field_path in fields_to_process:
            decision = await self._infer_field_value(field_path, user_message)

            if decision:
                decisions.append(decision)

                # Record decision
                await self._record_field_decision(decision)

                # Update state based on confidence
                if decision.confidence >= settings.confidence_threshold:
                    self.state.mark_field_resolved(field_path)
                else:
                    # Need user confirmation
                    questions.append(
                        f"For '{field_path}': I inferred '{decision.value}' "
                        f"(confidence: {decision.confidence:.0%}). "
                        f"Is this correct?"
                    )

        # Build response message
        if decisions:
            auto_accepted = [d for d in decisions if d.confidence >= settings.confidence_threshold]
            needs_review = [d for d in decisions if d.confidence < settings.confidence_threshold]

            message_parts = []
            if auto_accepted:
                message_parts.append(
                    f"Auto-populated {len(auto_accepted)} field(s) with high confidence."
                )
            if needs_review:
                message_parts.append(
                    f"{len(needs_review)} field(s) need your review."
                )

            message = " ".join(message_parts)
        else:
            message = "Processing fields..."

        return AgentResponse(
            message=message,
            field_decisions=decisions,
            questions=questions,
            needs_user_input=len(questions) > 0,
        )

    async def _generate_isa_structure(self) -> AgentResponse:
        """Generate ISA-Tab structure from collected data."""
        # Check if all required fields are resolved
        if self.state.fields_pending:
            return await self._process_pending_fields(None)

        # All fields resolved - ready to generate
        self.state.status = SessionStatus.COMPLETED
        self.state.termination_reason = TerminationReason.SUCCESS

        # Update confidence summary
        self.confidence_summary.update_stats()

        return AgentResponse(
            message=(
                f"ISA-Tab generation complete!\n"
                f"- {self.confidence_summary.auto_accepted} fields auto-accepted\n"
                f"- {self.confidence_summary.user_confirmed} fields user-confirmed\n"
                f"- {self.confidence_summary.user_edited} fields user-edited\n"
                f"- Average confidence: {self.confidence_summary.average_confidence:.0%}"
            ),
            is_complete=True,
        )

    async def _infer_field_value(
        self,
        field_path: str,
        user_message: str | None,
    ) -> FieldDecision | None:
        """Infer a value for a field using Pydantic AI agent.

        Args:
            field_path: Path to the field.
            user_message: Optional user input.

        Returns:
            Field decision or None if unable to infer.
        """
        # Build context for the agent
        context = self._build_field_context(field_path, user_message)
        
        try:
            # Run agent with conversation state
            result = await self.pydantic_agent.run(
                user_prompt=context,
                message_history=self.message_history,
                deps=self.state,
            )
            
            # Save LLM call record
            await self._save_llm_call_record(result, "field_inference", context)
            
            # Parse agent response into field decision
            # For now, return a simple decision based on the response
            # TODO: Enhance this to parse structured output from agent
            response_text = result.data if hasattr(result, 'data') else str(result)
            
            return FieldDecision(
                field_path=field_path,
                value=response_text,
                confidence=0.8,  # Default confidence
                justification="Inferred by LLM agent",
                source=FieldSource.LLM_INFERENCE,
            )
            
        except Exception as e:
            logger.error(
                "field_inference_error",
                field_path=field_path,
                error=str(e),
            )
            return None

    def _build_field_context(self, field_path: str, user_message: str | None) -> str:
        """Build context prompt for field inference.

        Args:
            field_path: Path to the field to infer.
            user_message: Optional user message.

        Returns:
            Context prompt string.
        """
        parts = [f"I need to determine the value for the field: {field_path}"]

        if self.state.metadata:
            parts.append(f"\nAvailable metadata: {self.state.metadata}")

        if user_message:
            parts.append(f"\nUser input: {user_message}")

        parts.append("\nPlease provide the most appropriate value for this field with justification.")

        return "\n".join(parts)

    async def _save_llm_call_record(self, agent_result, task: str, user_prompt: str) -> str:
        """Save LLM call record to database.

        Args:
            agent_result: Result from Pydantic AI agent run.
            task: Task description (e.g., 'field_inference').
            user_prompt: The user prompt that was sent.

        Returns:
            LLM call ID.
        """
        from isaforge.agents.prompts.versioning import compute_hash

        # Extract usage information
        usage = agent_result.usage() if hasattr(agent_result, 'usage') else None
        prompt_tokens = usage.request_tokens if usage else 0
        completion_tokens = usage.response_tokens if usage else 0

        # Compute user prompt hash
        user_prompt_hash = compute_hash(user_prompt)

        # Save to database
        llm_call_id = await session_manager.save_llm_call(
            session_id=self.state.session_id,
            task=task,
            model=settings.llm_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=0,  # TODO: Track actual latency
            system_prompt_hash=self.pydantic_agent.system_prompt_hash,
            user_prompt_hash=user_prompt_hash,
        )

        logger.debug(
            "llm_call_saved",
            call_id=llm_call_id,
            task=task,
            tokens=prompt_tokens + completion_tokens,
        )

        return llm_call_id

    async def _record_field_decision(self, decision: FieldDecision, llm_call_id: str | None = None) -> None:
        """Record a field decision in the database and confidence summary with auto-confidence snapshot.

        Args:
            decision: The field decision to record.
            llm_call_id: Optional LLM call ID that generated this decision.
        """
        # Determine user action based on confidence
        if decision.confidence >= settings.confidence_threshold:
            user_action = UserAction.AUTO_ACCEPTED
        else:
            user_action = UserAction.PENDING

        # Save to database
        decision_id = await session_manager.save_field_decision(
            session_id=self.state.session_id,
            field_path=decision.field_path,
            value=str(decision.value) if decision.value else None,
            confidence=decision.confidence,
            justification=decision.justification,
            source=decision.source.value,
            user_action=user_action.value,
            llm_call_id=llm_call_id,
            alternatives=[str(a) for a in decision.alternatives],
        )

        # Auto-snapshot confidence history
        await session_manager.save_confidence_history(
            field_decision_id=decision_id,
            confidence=decision.confidence,
            justification=decision.justification,
            source=decision.source.value,
            llm_call_id=llm_call_id,
        )

        # Update confidence summary
        self.confidence_summary.fields[decision.field_path] = FieldConfidence(
            field_path=decision.field_path,
            value=str(decision.value) if decision.value else None,
            confidence=decision.confidence,
            justification=decision.justification,
            source=decision.source,
            user_action=user_action,
            alternatives=[str(a) for a in decision.alternatives],
        )

    def _identify_required_fields(self) -> None:
        """Identify required fields based on ISA-Tab structure."""
        required_fields = [
            "study.identifier",
            "study.title",
            "study.description",
            "study.organism",
            "study.submission_date",
        ]

        for field in required_fields:
            self.state.mark_field_pending(field)

    def _build_metadata_summary(self, result: Any) -> str:
        """Build a summary of fetched metadata."""
        parts = [f"Fetched metadata for BioProject {result.accession}:"]

        if result.title:
            parts.append(f"- Title: {result.title[:100]}...")
        if result.organism:
            parts.append(f"- Organism: {result.organism}")
        if result.sample_count:
            parts.append(f"- Samples: {result.sample_count}")
        if result.experiment_count:
            parts.append(f"- Experiments: {result.experiment_count}")
        if result.linked_pubmed_ids:
            parts.append(f"- Linked publications: {len(result.linked_pubmed_ids)}")

        return "\n".join(parts)

    async def _handle_termination(
        self,
        reason: TerminationReason | None,
    ) -> AgentResponse:
        """Handle session termination."""
        self.state.status = SessionStatus.COMPLETED
        self.state.termination_reason = reason

        # Update session in database
        from isaforge.models.session import Session

        session = Session(
            id=self.state.session_id,
            bioproject_id=self.state.bioproject_id,
            local_metadata_paths=self.state.local_metadata_paths,
            output_path=self.state.output_path,
            status=self.state.status,
            termination_reason=self.state.termination_reason,
            turn_count=self.state.turn_count,
            total_tokens=self.state.total_prompt_tokens + self.state.total_completion_tokens,
            fields_resolved=self.state.fields_resolved,
            fields_pending=self.state.fields_pending,
            retry_counts=self.state.retry_counts,
        )
        await session_manager.update_session(session)

        if reason == TerminationReason.SUCCESS:
            message = "Generation completed successfully!"
        elif reason == TerminationReason.USER_EXIT:
            message = "Session ended by user request."
        elif reason == TerminationReason.STUCK:
            message = "Session ended: Unable to make further progress. Some fields could not be resolved."
        elif reason == TerminationReason.MAX_TURNS_EXCEEDED:
            message = f"Session ended: Maximum turns ({settings.max_conversation_turns}) exceeded."
        else:
            message = "Session ended."

        logger.info(
            "session_terminated",
            session_id=self.state.session_id,
            reason=reason.value if reason else "unknown",
        )

        return AgentResponse(
            message=message,
            is_complete=True,
        )

    def get_confidence_summary(self) -> ConfidenceSummary | None:
        """Get the current confidence summary."""
        if self.confidence_summary:
            self.confidence_summary.update_stats()
        return self.confidence_summary

    def get_state(self) -> ConversationState | None:
        """Get the current conversation state."""
        return self.state
