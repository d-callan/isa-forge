"""Custom exceptions for ISA-Forge."""


class ISAForgeError(Exception):
    """Base exception for ISA-Forge."""

    pass


class ConfigurationError(ISAForgeError):
    """Configuration-related errors."""

    pass


class RetrievalError(ISAForgeError):
    """Data retrieval errors."""

    pass


class NCBIError(RetrievalError):
    """NCBI API errors."""

    pass


class PublicationError(RetrievalError):
    """Publication retrieval/parsing errors."""

    pass


class OntologyError(ISAForgeError):
    """Ontology mapping errors."""

    pass


class OntologyServiceError(OntologyError):
    """Ontology service API errors."""

    pass


class OntologyMappingError(OntologyError):
    """Failed to map term to ontology."""

    pass


class SessionError(ISAForgeError):
    """Session management errors."""

    pass


class SessionNotFoundError(SessionError):
    """Session not found in database."""

    pass


class AgentError(ISAForgeError):
    """LLM agent errors."""

    pass


class AgentLoopError(AgentError):
    """Agent stuck in a loop or exceeded limits."""

    pass


class AgentTimeoutError(AgentError):
    """Agent exceeded time or turn limits."""

    pass


class ISABuildError(ISAForgeError):
    """ISA-Tab building errors."""

    pass


class ISAValidationError(ISABuildError):
    """ISA-Tab validation failed."""

    pass


class CircuitBreakerOpenError(ISAForgeError):
    """Circuit breaker is open due to repeated failures."""

    pass
