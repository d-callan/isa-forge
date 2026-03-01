"""Ontology mapping logic."""

from isaforge.core.config import settings
from isaforge.core.constants import CUSTOM_TERM_PREFIX
from isaforge.models.metadata.ontology import OntologyMapping, OntologyTerm
from isaforge.observability.logger import get_logger
from isaforge.ontology.base import BaseOntologyService
from isaforge.ontology.registry import OntologyRegistry

logger = get_logger(__name__)


class OntologyMapper:
    """Maps text to ontology terms using configured services."""

    def __init__(
        self,
        services: list[BaseOntologyService] | None = None,
        preferred_ontologies: list[str] | None = None,
    ):
        """Initialize the mapper.

        Args:
            services: List of ontology services to use. If None, uses registry.
            preferred_ontologies: Preferred ontologies for mapping.
        """
        self.services = services or []
        self.preferred_ontologies = preferred_ontologies or settings.preferred_ontologies
        self._custom_term_counter = 0

        # If no services provided, get from registry
        if not self.services:
            for name in OntologyRegistry.list_services():
                service = OntologyRegistry.get(name)
                if service:
                    self.services.append(service)

    async def map_term(
        self,
        text: str,
        context: str | None = None,
        ontologies: list[str] | None = None,
    ) -> OntologyMapping:
        """Map text to an ontology term.

        Args:
            text: Text to map.
            context: Optional context for better mapping.
            ontologies: Specific ontologies to search (overrides preferred).

        Returns:
            OntologyMapping with the best match and alternatives.
        """
        search_ontologies = ontologies or self.preferred_ontologies
        all_terms: list[tuple[OntologyTerm, str, float]] = []  # (term, source, score)

        # Search each service
        for service in self.services:
            try:
                terms = await service.search(
                    text,
                    ontologies=search_ontologies,
                    exact=False,
                    limit=5,
                )

                for i, term in enumerate(terms):
                    # Score based on position and ontology preference
                    base_score = 1.0 - (i * 0.1)  # Position penalty

                    # Boost for preferred ontologies
                    if term.ontology in self.preferred_ontologies:
                        pref_idx = self.preferred_ontologies.index(term.ontology)
                        base_score += 0.1 * (len(self.preferred_ontologies) - pref_idx)

                    # Boost for exact label match
                    if term.label.lower() == text.lower():
                        base_score += 0.3

                    all_terms.append((term, service.get_service_name(), base_score))

            except Exception as e:
                logger.warning(
                    "ontology_service_error",
                    service=service.get_service_name(),
                    error=str(e),
                )

        if not all_terms:
            # No matches found
            logger.info("no_ontology_match", text=text)
            return OntologyMapping(
                source_text=text,
                mapped_term=None,
                confidence=0.0,
                mapping_source="none",
                alternatives=[],
                justification=f"No ontology term found for '{text}'",
            )

        # Sort by score
        all_terms.sort(key=lambda x: x[2], reverse=True)

        # Best match
        best_term, best_source, best_score = all_terms[0]

        # Normalize confidence to 0-1
        confidence = min(best_score / 1.5, 1.0)

        # Get alternatives (excluding best)
        alternatives = [t[0] for t in all_terms[1:5]]

        # Generate justification
        justification = self._generate_justification(text, best_term, best_source, confidence)

        logger.info(
            "ontology_mapped",
            text=text,
            term_id=best_term.term_id,
            confidence=confidence,
            source=best_source,
        )

        return OntologyMapping(
            source_text=text,
            mapped_term=best_term,
            confidence=confidence,
            mapping_source=best_source,
            alternatives=alternatives,
            justification=justification,
        )

    def _generate_justification(
        self,
        text: str,
        term: OntologyTerm,
        source: str,
        confidence: float,
    ) -> str:
        """Generate a justification for the mapping.

        Args:
            text: Original text.
            term: Mapped term.
            source: Service that provided the mapping.
            confidence: Confidence score.

        Returns:
            Human-readable justification.
        """
        parts = []

        if term.label.lower() == text.lower():
            parts.append(f"Exact label match for '{text}'")
        else:
            parts.append(f"Mapped '{text}' to '{term.label}'")

        parts.append(f"from {term.ontology} ontology")
        parts.append(f"via {source}")

        if confidence >= 0.9:
            parts.append("(high confidence)")
        elif confidence >= 0.7:
            parts.append("(medium confidence)")
        else:
            parts.append("(low confidence - review recommended)")

        return " ".join(parts)

    def generate_custom_term(
        self,
        text: str,
        definition: str | None = None,
    ) -> OntologyTerm:
        """Generate a custom term ID for unmapped text.

        Args:
            text: The text that couldn't be mapped.
            definition: Optional definition for the term.

        Returns:
            A custom OntologyTerm with generated ID.
        """
        self._custom_term_counter += 1
        term_id = f"{CUSTOM_TERM_PREFIX}:{self._custom_term_counter:06d}"

        logger.info(
            "custom_term_generated",
            text=text,
            term_id=term_id,
        )

        return OntologyTerm(
            label=text,
            term_id=term_id,
            ontology=CUSTOM_TERM_PREFIX,
            iri=None,
            description=definition,
            synonyms=[],
            is_custom=True,
        )

    async def map_or_create_custom(
        self,
        text: str,
        min_confidence: float = 0.5,
        ontologies: list[str] | None = None,
    ) -> OntologyMapping:
        """Map text to ontology term, creating custom term if no good match.

        Args:
            text: Text to map.
            min_confidence: Minimum confidence to accept a mapping.
            ontologies: Specific ontologies to search.

        Returns:
            OntologyMapping with either a found term or custom term.
        """
        mapping = await self.map_term(text, ontologies=ontologies)

        if mapping.mapped_term is None or mapping.confidence < min_confidence:
            # Create custom term
            custom_term = self.generate_custom_term(text)
            return OntologyMapping(
                source_text=text,
                mapped_term=custom_term,
                confidence=0.0,
                mapping_source="custom",
                alternatives=mapping.alternatives if mapping.mapped_term else [],
                justification=(
                    f"No suitable ontology term found for '{text}' "
                    f"(best match confidence: {mapping.confidence:.2f}). "
                    f"Created custom term {custom_term.term_id}."
                ),
            )

        return mapping

    async def map_batch(
        self,
        texts: list[str],
        ontologies: list[str] | None = None,
    ) -> dict[str, OntologyMapping]:
        """Map multiple texts to ontology terms.

        Args:
            texts: List of texts to map.
            ontologies: Specific ontologies to search.

        Returns:
            Dictionary mapping input text to OntologyMapping.
        """
        results = {}
        for text in texts:
            results[text] = await self.map_term(text, ontologies=ontologies)
        return results
