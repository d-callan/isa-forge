"""Zooma annotation service client."""

import httpx

from isaforge.core.config import settings
from isaforge.core.exceptions import OntologyServiceError
from isaforge.models.metadata.ontology import OntologyTerm
from isaforge.observability.circuit_breaker import CircuitBreakerRegistry
from isaforge.observability.logger import get_logger
from isaforge.observability.metrics import Timer
from isaforge.ontology.base import BaseOntologyService

logger = get_logger(__name__)

# Circuit breaker for Zooma API
zooma_circuit_breaker = CircuitBreakerRegistry.get_or_create(
    "zooma_api",
    max_failures=3,
    timeout_seconds=60.0,
)


class ZoomaService(BaseOntologyService):
    """Client for the EBI Zooma annotation service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the Zooma client.

        Args:
            base_url: Zooma API base URL.
            timeout: Request timeout in seconds.
        """
        self.base_url = (base_url or settings.zooma_base_url).rstrip("/")
        self.timeout = timeout

    async def _request(self, endpoint: str, params: dict | None = None) -> list | dict:
        """Make an async HTTP request to Zooma.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response.

        Raises:
            OntologyServiceError: If the request fails.
        """
        url = f"{self.base_url}/{endpoint}"

        async def _do_request() -> list | dict:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with Timer("zooma_request", {"endpoint": endpoint}):
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

        try:
            return await zooma_circuit_breaker.call_async(_do_request)
        except httpx.HTTPStatusError as e:
            logger.error(
                "zooma_http_error",
                endpoint=endpoint,
                status_code=e.response.status_code,
            )
            raise OntologyServiceError(f"Zooma API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("zooma_request_error", endpoint=endpoint, error=str(e))
            raise OntologyServiceError(f"Zooma request failed: {e}") from e

    def _parse_annotation(self, annotation: dict) -> OntologyTerm | None:
        """Parse Zooma annotation into OntologyTerm.

        Args:
            annotation: Annotation data from Zooma.

        Returns:
            Parsed OntologyTerm, or None if invalid.
        """
        semantic_tags = annotation.get("semanticTags", [])
        if not semantic_tags:
            return None

        # Get the first semantic tag (IRI)
        iri = semantic_tags[0]

        # Extract term ID from IRI
        # Common patterns: .../OBI_0000070 or .../EFO_0000001
        term_id = ""
        ontology = ""

        if "/" in iri:
            last_part = iri.rsplit("/", 1)[-1]
            if "_" in last_part:
                parts = last_part.split("_", 1)
                ontology = parts[0]
                term_id = f"{ontology}:{parts[1]}"
            else:
                term_id = last_part

        # Get label from annotated property
        annotated_property = annotation.get("annotatedProperty", {})
        label = annotated_property.get("propertyValue", "")

        if not term_id or not label:
            return None

        return OntologyTerm(
            label=label,
            term_id=term_id,
            ontology=ontology.upper(),
            iri=iri,
            description=None,
            synonyms=[],
            is_custom=False,
        )

    async def search(
        self,
        query: str,
        ontologies: list[str] | None = None,
        exact: bool = False,
        limit: int = 10,
    ) -> list[OntologyTerm]:
        """Search for ontology terms using Zooma annotation.

        Args:
            query: Search query string (property value to annotate).
            ontologies: List of ontology names to filter results.
            exact: If True, only return high-confidence matches.
            limit: Maximum number of results.

        Returns:
            List of matching ontology terms.
        """
        params = {"propertyValue": query}

        if ontologies:
            params["ontologies"] = ",".join(o.lower() for o in ontologies)

        try:
            data = await self._request("services/annotate", params)

            if not isinstance(data, list):
                return []

            terms = []
            seen_iris = set()

            for annotation in data:
                # Filter by confidence if exact match requested
                if exact:
                    confidence = annotation.get("confidence", "")
                    if confidence not in ["HIGH", "GOOD"]:
                        continue

                term = self._parse_annotation(annotation)
                if term and term.iri not in seen_iris:
                    seen_iris.add(term.iri)
                    terms.append(term)

                    if len(terms) >= limit:
                        break

            logger.info(
                "zooma_search_completed",
                query=query,
                result_count=len(terms),
            )

            return terms

        except OntologyServiceError:
            raise
        except Exception as e:
            raise OntologyServiceError(f"Zooma search failed: {e}") from e

    async def get_term(self, term_id: str) -> OntologyTerm | None:
        """Get a specific ontology term by ID.

        Note: Zooma doesn't support direct term lookup by ID.
        This method searches for the term ID as a query.

        Args:
            term_id: The ontology term ID (e.g., 'OBI:0000070').

        Returns:
            The ontology term, or None if not found.
        """
        # Zooma doesn't have direct term lookup, search instead
        terms = await self.search(term_id, exact=True, limit=1)
        return terms[0] if terms else None

    async def get_term_by_iri(self, iri: str) -> OntologyTerm | None:
        """Get a specific ontology term by IRI.

        Note: Zooma doesn't support direct IRI lookup.

        Args:
            iri: The full IRI of the term.

        Returns:
            None (not supported by Zooma).
        """
        # Zooma doesn't support IRI lookup
        return None

    def get_service_name(self) -> str:
        """Get the service name.

        Returns:
            'zooma'
        """
        return "zooma"

    async def is_available(self) -> bool:
        """Check if Zooma is available.

        Returns:
            True if Zooma is reachable.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Simple health check
                response = await client.get(
                    f"{self.base_url}/services/annotate",
                    params={"propertyValue": "test"},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def annotate_with_confidence(
        self,
        text: str,
        ontologies: list[str] | None = None,
    ) -> list[dict]:
        """Get annotations with confidence scores.

        Args:
            text: Text to annotate.
            ontologies: List of ontology names to filter.

        Returns:
            List of annotations with confidence information.
        """
        params = {"propertyValue": text}

        if ontologies:
            params["ontologies"] = ",".join(o.lower() for o in ontologies)

        try:
            data = await self._request("services/annotate", params)

            if not isinstance(data, list):
                return []

            results = []
            for annotation in data:
                term = self._parse_annotation(annotation)
                if term:
                    results.append({
                        "term": term,
                        "confidence": annotation.get("confidence", "LOW"),
                        "source": annotation.get("derivedFrom", {}).get("name", "unknown"),
                    })

            return results

        except Exception as e:
            logger.warning("zooma_annotate_error", text=text, error=str(e))
            return []
