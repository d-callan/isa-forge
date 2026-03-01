"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ISA-Forge configuration settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ISAFORGE_",
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: Literal["anthropic", "google", "ollama"] = Field(
        default="anthropic",
        description="LLM provider to use",
    )
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model name for the LLM provider",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )
    google_api_key: str | None = Field(
        default=None,
        description="Google AI API key",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server base URL",
    )

    # Session Storage
    session_db_path: Path = Field(
        default=Path.home() / ".isaforge" / "sessions.db",
        description="Path to SQLite session database",
    )

    # NCBI API
    ncbi_api_key: str | None = Field(
        default=None,
        description="NCBI API key for higher rate limits",
    )
    ncbi_email: str | None = Field(
        default=None,
        description="Email for NCBI API identification",
    )

    # Ontology Services
    ols_base_url: str = Field(
        default="https://www.ebi.ac.uk/ols4/api",
        description="OLS API base URL",
    )
    zooma_base_url: str = Field(
        default="https://www.ebi.ac.uk/spot/zooma/v2/api",
        description="Zooma API base URL",
    )
    preferred_ontologies: list[str] = Field(
        default=["OBI", "EFO", "NCIT", "UBERON", "CL", "CHEBI"],
        description="Preferred ontologies for term mapping",
    )

    # Behavior
    max_publications: int = Field(
        default=6,
        ge=1,
        le=20,
        description="Maximum publications to retrieve per BioProject",
    )
    confidence_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for auto-accepting fields",
    )
    max_conversation_turns: int = Field(
        default=50,
        ge=1,
        description="Maximum conversation turns before termination",
    )
    max_tool_calls_per_turn: int = Field(
        default=10,
        ge=1,
        description="Maximum tool calls per conversation turn",
    )
    max_retries_per_field: int = Field(
        default=3,
        ge=1,
        description="Maximum retries for resolving a field",
    )

    # Output
    generate_methods: bool = Field(
        default=True,
        description="Generate methods.md output",
    )
    generate_chat_log: bool = Field(
        default=True,
        description="Generate chat_log.md output",
    )
    validation_strict: bool = Field(
        default=False,
        description="Use strict ISA-Tab validation",
    )

    # Observability
    enable_tracing: bool = Field(
        default=False,
        description="Enable LLM tracing (requires langsmith)",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )


# Global settings instance
settings = Settings()
