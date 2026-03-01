"""Abstract base class for ontology services."""

from abc import ABC, abstractmethod

from isaforge.models.metadata.ontology import OntologyTerm


class BaseOntologyService(ABC):
    """Abstract base class for ontology lookup services."""

    @abstractmethod
    async def search(
        self,
        query: str,
        ontologies: list[str] | None = None,
        exact: bool = False,
        limit: int = 10,
    ) -> list[OntologyTerm]:
        """Search for ontology terms matching a query.

        Args:
            query: Search query string.
            ontologies: List of ontology names to search (e.g., ['OBI', 'EFO']).
            exact: If True, only return exact matches.
            limit: Maximum number of results.

        Returns:
            List of matching ontology terms.
        """
        pass

    @abstractmethod
    async def get_term(self, term_id: str) -> OntologyTerm | None:
        """Get a specific ontology term by ID.

        Args:
            term_id: The ontology term ID (e.g., 'OBI:0000070').

        Returns:
            The ontology term, or None if not found.
        """
        pass

    @abstractmethod
    async def get_term_by_iri(self, iri: str) -> OntologyTerm | None:
        """Get a specific ontology term by IRI.

        Args:
            iri: The full IRI of the term.

        Returns:
            The ontology term, or None if not found.
        """
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """Get the name of this ontology service.

        Returns:
            Name of the service (e.g., 'ols', 'zooma').
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the service is available.

        Returns:
            True if the service is reachable.
        """
        pass
