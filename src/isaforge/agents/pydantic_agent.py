"""Pydantic AI agent wrapper for ISA-Forge."""

import asyncio
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage

from isaforge.agents.prompts.system import SYSTEM_PROMPT
from isaforge.agents.prompts.versioning import get_prompt_registry
from isaforge.agents.state import ConversationState
from isaforge.agents.tools.metadata_tools import (
    FetchBioProjectInput,
    FetchPublicationsInput,
    ParseLocalFileInput,
    fetch_bioproject_metadata,
    fetch_publications as fetch_pubs_tool,
    parse_local_file as parse_file_tool,
)
from isaforge.agents.tools.ontology_tools import (
    MapTermInput,
    SearchOntologyInput,
    map_term_to_ontology as map_term_tool,
    search_ontology,
)
from isaforge.core.config import settings
from isaforge.observability.circuit_breaker import CircuitBreakerRegistry
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class ISAForgeAgent:
    """Pydantic AI agent wrapper for ISA-Forge field inference."""

    def __init__(self, session_id: str):
        """Initialize the agent.

        Args:
            session_id: Session ID for tracking.
        """
        self.session_id = session_id

        # Register system prompt with versioning
        registry = get_prompt_registry()
        system_prompt_version = registry.register("system_prompt", SYSTEM_PROMPT)
        self.system_prompt_hash = system_prompt_version.content_hash

        # Use model from settings (configured via .env)
        model_name = f"{settings.llm_provider}:{settings.llm_model}"

        # Create Pydantic AI agent
        self.agent = Agent(
            model=model_name,
            deps_type=ConversationState,
            system_prompt=SYSTEM_PROMPT,
        )

        # Register all tools
        self._register_tools()

    def _register_tools(self):
        """Register all available tools with the agent."""

        @self.agent.tool
        async def fetch_bioproject(
            ctx: RunContext[ConversationState], bioproject_id: str
        ) -> dict[str, Any]:
            """Fetch BioProject metadata from NCBI.

            Args:
                ctx: Runtime context with conversation state.
                bioproject_id: BioProject accession (e.g., PRJNA123456).

            Returns:
                BioProject metadata or error information.
            """
            result = await fetch_bioproject_metadata(
                FetchBioProjectInput(bioproject_id=bioproject_id)
            )
            return result.model_dump()

        @self.agent.tool
        async def fetch_publications(
            ctx: RunContext[ConversationState], pmids: list[str], max_count: int = 6
        ) -> dict[str, Any]:
            """Fetch publication details from PubMed.

            Args:
                ctx: Runtime context with conversation state.
                pmids: List of PubMed IDs to fetch.
                max_count: Maximum number of publications to fetch.

            Returns:
                Publication metadata or error information.
            """
            result = await fetch_pubs_tool(
                FetchPublicationsInput(pmids=pmids, max_count=max_count)
            )
            return result.model_dump()

        @self.agent.tool
        async def parse_local_file(
            ctx: RunContext[ConversationState], file_path: str
        ) -> dict[str, Any]:
            """Parse local metadata file (CSV, JSON, TSV).

            Args:
                ctx: Runtime context with conversation state.
                file_path: Path to the file to parse.

            Returns:
                Parsed file data or error information.
            """
            result = await parse_file_tool(ParseLocalFileInput(file_path=file_path))
            return result.model_dump()

        @self.agent.tool
        async def search_ontology_terms(
            ctx: RunContext[ConversationState],
            query: str,
            ontologies: list[str] | None = None,
            limit: int = 5,
        ) -> dict[str, Any]:
            """Search for ontology terms.

            Args:
                ctx: Runtime context with conversation state.
                query: Text to search for in ontologies.
                ontologies: Specific ontologies to search (e.g., ['OBI', 'EFO']).
                limit: Maximum number of results.

            Returns:
                Matching ontology terms or error information.
            """
            result = await search_ontology(
                SearchOntologyInput(query=query, ontologies=ontologies, limit=limit)
            )
            return result.model_dump()

        @self.agent.tool
        async def map_term_to_ontology(
            ctx: RunContext[ConversationState], term: str, context: str = ""
        ) -> dict[str, Any]:
            """Map a term to an ontology.

            Args:
                ctx: Runtime context with conversation state.
                term: Term to map.
                context: Additional context about the term.

            Returns:
                Ontology mapping result or error information.
            """
            result = await map_term_tool(
                MapTermInput(term=term, context=context)
            )
            return result.model_dump()

    async def run_streaming(
        self,
        user_prompt: str,
        message_history: list[dict],
        deps: ConversationState,
    ):
        """Run agent with streaming support.

        Args:
            user_prompt: User's message/prompt.
            message_history: Previous conversation messages.
            deps: Conversation state dependencies.

        Yields:
            Tuple of (text_chunk, final_result) where final_result is None until the end.
        """
        # Convert message history to Pydantic AI format
        messages = self._convert_message_history(message_history)

        logger.info(
            "agent_run_streaming_start",
            session_id=self.session_id,
            message_count=len(messages),
        )

        # Stream agent response
        async with self.agent.run_stream(
            user_prompt=user_prompt,
            message_history=messages,
            deps=deps,
        ) as stream:
            # Stream text chunks
            async for chunk in stream.stream_text():
                yield chunk, None

            # Get final result
            result = await stream.get_data()

            logger.info(
                "agent_run_streaming_complete",
                session_id=self.session_id,
                usage=result.usage(),
            )

            # Yield final result as last item
            yield None, result

    async def run(
        self,
        user_prompt: str,
        message_history: list[dict],
        deps: ConversationState,
        max_retries: int = 3,
    ):
        """Run agent with retry logic and circuit breaker.

        Args:
            user_prompt: User's message/prompt.
            message_history: Previous conversation messages.
            deps: Conversation state dependencies.
            max_retries: Maximum number of retry attempts.

        Returns:
            Agent result.
        """
        # Get circuit breaker for this LLM provider
        circuit_breaker = CircuitBreakerRegistry.get_or_create(
            f"llm_{settings.llm_provider}"
        )

        # Convert message history to Pydantic AI format
        messages = self._convert_message_history(message_history)

        logger.info(
            "agent_run_start",
            session_id=self.session_id,
            message_count=len(messages),
        )

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                # Run through circuit breaker
                async with circuit_breaker:
                    result = await self.agent.run(
                        user_prompt=user_prompt,
                        message_history=messages,
                        deps=deps,
                    )

                logger.info(
                    "agent_run_complete",
                    session_id=self.session_id,
                    usage=result.usage(),
                    attempt=attempt + 1,
                )

                return result

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        "agent_run_failed_after_retries",
                        session_id=self.session_id,
                        attempts=max_retries,
                        error=str(e),
                    )
                    raise

                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(
                    "agent_run_retry",
                    session_id=self.session_id,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)

    def _convert_message_history(self, message_history: list[dict]) -> list[ModelMessage]:
        """Convert message history from dict format to Pydantic AI format.

        Args:
            message_history: List of message dictionaries with 'role' and 'content'.

        Returns:
            List of ModelMessage objects.
        """
        # For now, return empty list - Pydantic AI will handle message history
        # through the run context. We'll enhance this if needed.
        return []
