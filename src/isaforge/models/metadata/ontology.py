"""Ontology term Pydantic model."""

from pydantic import BaseModel, Field


class OntologyTerm(BaseModel):
    """An ontology term with its metadata."""

    label: str = Field(..., description="Human-readable term label")
    term_id: str = Field(..., description="Ontology term ID (e.g., 'OBI:0000070')")
    ontology: str = Field(..., description="Ontology name (e.g., 'OBI')")
    iri: str | None = Field(default=None, description="Full IRI of the term")
    description: str | None = Field(default=None, description="Term description")
    synonyms: list[str] = Field(default_factory=list, description="Term synonyms")
    is_custom: bool = Field(
        default=False, description="Whether this is a custom (non-standard) term"
    )


class OntologyMapping(BaseModel):
    """A mapping from a source term to an ontology term."""

    source_text: str = Field(..., description="Original text being mapped")
    mapped_term: OntologyTerm | None = Field(
        default=None, description="Mapped ontology term, if found"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in the mapping"
    )
    mapping_source: str = Field(
        default="unknown", description="Source of the mapping (e.g., 'ols', 'zooma', 'llm')"
    )
    alternatives: list[OntologyTerm] = Field(
        default_factory=list, description="Alternative mappings considered"
    )
    justification: str | None = Field(
        default=None, description="Explanation for the mapping choice"
    )
