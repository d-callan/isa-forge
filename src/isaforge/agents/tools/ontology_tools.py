"""Agent tools for ontology mapping."""

from pydantic import BaseModel, Field

from isaforge.models.metadata.ontology import OntologyTerm
from isaforge.observability.logger import get_logger
from isaforge.ontology.mapper import OntologyMapper
from isaforge.ontology.registry import setup_default_services

logger = get_logger(__name__)


class SearchOntologyInput(BaseModel):
    """Input for searching ontology terms."""

    query: str = Field(..., description="Text to search for in ontologies")
    ontologies: list[str] | None = Field(
        default=None,
        description="Specific ontologies to search (e.g., ['OBI', 'EFO'])",
    )
    limit: int = Field(default=5, description="Maximum number of results")


class OntologyTermResult(BaseModel):
    """A single ontology term result."""

    label: str
    term_id: str
    ontology: str
    description: str | None = None
    is_custom: bool = False


class SearchOntologyOutput(BaseModel):
    """Output from ontology search."""

    success: bool
    query: str
    results: list[OntologyTermResult] = Field(default_factory=list)
    error: str | None = None


async def search_ontology(input_data: SearchOntologyInput) -> SearchOntologyOutput:
    """Search for ontology terms matching a query.

    Args:
        input_data: Input containing the search query.

    Returns:
        Matching ontology terms or error information.
    """
    try:
        # Ensure services are set up
        setup_default_services()

        mapper = OntologyMapper()
        mapping = await mapper.map_term(
            input_data.query,
            ontologies=input_data.ontologies,
        )

        results = []

        # Add best match if found
        if mapping.mapped_term:
            results.append(
                OntologyTermResult(
                    label=mapping.mapped_term.label,
                    term_id=mapping.mapped_term.term_id,
                    ontology=mapping.mapped_term.ontology,
                    description=mapping.mapped_term.description,
                    is_custom=mapping.mapped_term.is_custom,
                )
            )

        # Add alternatives
        for alt in mapping.alternatives[: input_data.limit - 1]:
            results.append(
                OntologyTermResult(
                    label=alt.label,
                    term_id=alt.term_id,
                    ontology=alt.ontology,
                    description=alt.description,
                    is_custom=alt.is_custom,
                )
            )

        logger.info(
            "ontology_search_tool_success",
            query=input_data.query,
            result_count=len(results),
        )

        return SearchOntologyOutput(
            success=True,
            query=input_data.query,
            results=results,
        )

    except Exception as e:
        logger.error("ontology_search_tool_error", query=input_data.query, error=str(e))
        return SearchOntologyOutput(
            success=False,
            query=input_data.query,
            error=str(e),
        )


class MapTermInput(BaseModel):
    """Input for mapping a term to ontology."""

    text: str = Field(..., description="Text to map to an ontology term")
    min_confidence: float = Field(
        default=0.5,
        description="Minimum confidence to accept a mapping",
    )
    create_custom_if_needed: bool = Field(
        default=True,
        description="Create a custom term if no good match found",
    )


class MapTermOutput(BaseModel):
    """Output from term mapping."""

    success: bool
    source_text: str
    mapped_term: OntologyTermResult | None = None
    confidence: float = 0.0
    justification: str | None = None
    alternatives: list[OntologyTermResult] = Field(default_factory=list)
    error: str | None = None


async def map_term_to_ontology(input_data: MapTermInput) -> MapTermOutput:
    """Map text to an ontology term.

    Args:
        input_data: Input containing the text to map.

    Returns:
        Mapping result with confidence and alternatives.
    """
    try:
        setup_default_services()

        mapper = OntologyMapper()

        if input_data.create_custom_if_needed:
            mapping = await mapper.map_or_create_custom(
                input_data.text,
                min_confidence=input_data.min_confidence,
            )
        else:
            mapping = await mapper.map_term(input_data.text)

        mapped_term = None
        if mapping.mapped_term:
            mapped_term = OntologyTermResult(
                label=mapping.mapped_term.label,
                term_id=mapping.mapped_term.term_id,
                ontology=mapping.mapped_term.ontology,
                description=mapping.mapped_term.description,
                is_custom=mapping.mapped_term.is_custom,
            )

        alternatives = [
            OntologyTermResult(
                label=alt.label,
                term_id=alt.term_id,
                ontology=alt.ontology,
                description=alt.description,
                is_custom=alt.is_custom,
            )
            for alt in mapping.alternatives[:3]
        ]

        logger.info(
            "map_term_tool_success",
            text=input_data.text,
            term_id=mapped_term.term_id if mapped_term else None,
            confidence=mapping.confidence,
        )

        return MapTermOutput(
            success=True,
            source_text=input_data.text,
            mapped_term=mapped_term,
            confidence=mapping.confidence,
            justification=mapping.justification,
            alternatives=alternatives,
        )

    except Exception as e:
        logger.error("map_term_tool_error", text=input_data.text, error=str(e))
        return MapTermOutput(
            success=False,
            source_text=input_data.text,
            error=str(e),
        )


class BatchMapTermsInput(BaseModel):
    """Input for batch mapping terms."""

    terms: list[str] = Field(..., description="List of terms to map")
    min_confidence: float = Field(default=0.5)


class BatchMapTermsOutput(BaseModel):
    """Output from batch term mapping."""

    success: bool
    mappings: dict[str, MapTermOutput] = Field(default_factory=dict)
    error: str | None = None


async def batch_map_terms(input_data: BatchMapTermsInput) -> BatchMapTermsOutput:
    """Map multiple terms to ontology terms.

    Args:
        input_data: Input containing terms to map.

    Returns:
        Mapping results for all terms.
    """
    try:
        mappings = {}
        for term in input_data.terms:
            result = await map_term_to_ontology(
                MapTermInput(
                    text=term,
                    min_confidence=input_data.min_confidence,
                )
            )
            mappings[term] = result

        logger.info(
            "batch_map_tool_success",
            term_count=len(input_data.terms),
        )

        return BatchMapTermsOutput(
            success=True,
            mappings=mappings,
        )

    except Exception as e:
        logger.error("batch_map_tool_error", error=str(e))
        return BatchMapTermsOutput(
            success=False,
            error=str(e),
        )
