"""Custom term management for unmapped ontology terms."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from isaforge.core.constants import CUSTOM_TERM_PREFIX
from isaforge.models.metadata.ontology import OntologyTerm
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class CustomTermDefinition(BaseModel):
    """Definition for a custom ontology term."""

    term_id: str = Field(..., description="Custom term ID")
    label: str = Field(..., description="Term label")
    definition: str | None = Field(default=None, description="Term definition")
    source_text: str = Field(..., description="Original text that was mapped")
    context: str | None = Field(default=None, description="Context where term was used")
    suggested_ontologies: list[str] = Field(
        default_factory=list, description="Ontologies that might contain similar terms"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="isaforge", description="Creator of the term")
    notes: str | None = Field(default=None, description="Additional notes")


class DataDictionary(BaseModel):
    """Data dictionary containing custom term definitions."""

    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    terms: dict[str, CustomTermDefinition] = Field(
        default_factory=dict, description="Custom terms by ID"
    )

    def add_term(
        self,
        term: OntologyTerm,
        source_text: str,
        definition: str | None = None,
        context: str | None = None,
        suggested_ontologies: list[str] | None = None,
    ) -> CustomTermDefinition:
        """Add a custom term to the dictionary.

        Args:
            term: The custom OntologyTerm.
            source_text: Original text that was mapped.
            definition: Optional definition.
            context: Optional context.
            suggested_ontologies: Ontologies that might have similar terms.

        Returns:
            The created CustomTermDefinition.
        """
        term_def = CustomTermDefinition(
            term_id=term.term_id,
            label=term.label,
            definition=definition or term.description,
            source_text=source_text,
            context=context,
            suggested_ontologies=suggested_ontologies or [],
        )
        self.terms[term.term_id] = term_def

        logger.info(
            "custom_term_added_to_dictionary",
            term_id=term.term_id,
            label=term.label,
        )

        return term_def

    def get_term(self, term_id: str) -> CustomTermDefinition | None:
        """Get a custom term definition.

        Args:
            term_id: The term ID.

        Returns:
            The term definition, or None if not found.
        """
        return self.terms.get(term_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export.

        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "term_count": len(self.terms),
            "terms": {
                term_id: {
                    "term_id": term_def.term_id,
                    "label": term_def.label,
                    "definition": term_def.definition,
                    "source_text": term_def.source_text,
                    "context": term_def.context,
                    "suggested_ontologies": term_def.suggested_ontologies,
                    "created_at": term_def.created_at.isoformat(),
                    "notes": term_def.notes,
                }
                for term_id, term_def in self.terms.items()
            },
        }


class CustomTermGenerator:
    """Generator for custom term IDs."""

    def __init__(self, prefix: str = CUSTOM_TERM_PREFIX):
        """Initialize the generator.

        Args:
            prefix: Prefix for custom term IDs.
        """
        self.prefix = prefix
        self._counter = 0

    def generate_id(self) -> str:
        """Generate a new custom term ID.

        Returns:
            A unique custom term ID.
        """
        self._counter += 1
        return f"{self.prefix}:{self._counter:06d}"

    def create_term(
        self,
        label: str,
        definition: str | None = None,
    ) -> OntologyTerm:
        """Create a new custom ontology term.

        Args:
            label: Term label.
            definition: Optional definition.

        Returns:
            A new custom OntologyTerm.
        """
        term_id = self.generate_id()

        return OntologyTerm(
            label=label,
            term_id=term_id,
            ontology=self.prefix,
            iri=None,
            description=definition,
            synonyms=[],
            is_custom=True,
        )

    def reset(self) -> None:
        """Reset the counter."""
        self._counter = 0
