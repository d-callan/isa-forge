"""OLS (Ontology Lookup Service) client."""

from urllib.parse import quote

import httpx

from isaforge.core.config import settings
from isaforge.core.exceptions import OntologyServiceError
from isaforge.models.metadata.ontology import OntologyTerm
from isaforge.observability.circuit_breaker import CircuitBreakerRegistry
from isaforge.observability.logger import get_logger
from isaforge.observability.metrics import Timer
from isaforge.ontology.base import BaseOntologyService

logger = get_logger(__name__)

# Circuit breaker for OLS API
ols_circuit_breaker = CircuitBreakerRegistry.get_or_create(
    "ols_api",
    max_failures=3,
    timeout_seconds=60.0,
)


class OLSService(BaseOntologyService):
    """Client for the EBI Ontology Lookup Service (OLS4)."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the OLS client.

        Args:
            base_url: OLS API base URL.
            timeout: Request timeout in seconds.
        """
        self.base_url = (base_url or settings.ols_base_url).rstrip("/")
        self.timeout = timeout

    async def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make an async HTTP request to OLS.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            OntologyServiceError: If the request fails.
        """
        url = f"{self.base_url}/{endpoint}"

        async def _do_request() -> dict:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with Timer("ols_request", {"endpoint": endpoint}):
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

        try:
            return await ols_circuit_breaker.call_async(_do_request)
        except httpx.HTTPStatusError as e:
            logger.error(
                "ols_http_error",
                endpoint=endpoint,
                status_code=e.response.status_code,
            )
            raise OntologyServiceError(f"OLS API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("ols_request_error", endpoint=endpoint, error=str(e))
            raise OntologyServiceError(f"OLS request failed: {e}") from e

    def _parse_term(self, data: dict) -> OntologyTerm:
        """Parse OLS term response into OntologyTerm model.

        Args:
            data: Term data from OLS.

        Returns:
            Parsed OntologyTerm.
        """
        # Extract ontology from IRI or obo_id
        obo_id = data.get("obo_id", "")
        ontology = obo_id.split(":")[0] if ":" in obo_id else data.get("ontology_name", "")

        return OntologyTerm(
            label=data.get("label", ""),
            term_id=obo_id or data.get("short_form", ""),
            ontology=ontology.upper(),
            iri=data.get("iri"),
            description=data.get("description", [""])[0] if data.get("description") else None,
            synonyms=data.get("synonyms", []) or [],
            is_custom=False,
        )

    async def search(
        self,
        query: str,
        ontologies: list[str] | None = None,
        exact: bool = False,
        limit: int = 10,
    ) -> list[OntologyTerm]:
        """Search for ontology terms.

        Args:
            query: Search query string.
            ontologies: List of ontology names to search.
            exact: If True, only return exact matches.
            limit: Maximum number of results.

        Returns:
            List of matching ontology terms.
        """
        params = {
            "q": query,
            "rows": limit,
            "exact": str(exact).lower(),
        }

        if ontologies:
            params["ontology"] = ",".join(o.lower() for o in ontologies)

        try:
            data = await self._request("search", params)
            docs = data.get("response", {}).get("docs", [])

            terms = []
            for doc in docs:
                try:
                    term = self._parse_term(doc)
                    terms.append(term)
                except Exception as e:
                    logger.debug("ols_parse_error", error=str(e), doc=doc)

            logger.info(
                "ols_search_completed",
                query=query,
                result_count=len(terms),
            )

            return terms

        except OntologyServiceError:
            raise
        except Exception as e:
            raise OntologyServiceError(f"OLS search failed: {e}") from e

    async def get_term(self, term_id: str) -> OntologyTerm | None:
        """Get a specific ontology term by ID.

        Args:
            term_id: The ontology term ID (e.g., 'OBI:0000070').

        Returns:
            The ontology term, or None if not found.
        """
        if ":" not in term_id:
            return None

        ontology, local_id = term_id.split(":", 1)
        ontology = ontology.lower()

        try:
            # OLS4 uses double-encoded IRIs
            iri = f"http://purl.obolibrary.org/obo/{ontology.upper()}_{local_id}"
            encoded_iri = quote(quote(iri, safe=""), safe="")

            data = await self._request(f"ontologies/{ontology}/terms/{encoded_iri}")

            if data:
                return self._parse_term(data)
            return None

        except OntologyServiceError:
            return None
        except Exception as e:
            logger.debug("ols_get_term_error", term_id=term_id, error=str(e))
            return None

    async def get_term_by_iri(self, iri: str) -> OntologyTerm | None:
        """Get a specific ontology term by IRI.

        Args:
            iri: The full IRI of the term.

        Returns:
            The ontology term, or None if not found.
        """
        try:
            encoded_iri = quote(quote(iri, safe=""), safe="")
            data = await self._request(f"terms/{encoded_iri}")

            if data:
                return self._parse_term(data)
            return None

        except OntologyServiceError:
            return None
        except Exception as e:
            logger.debug("ols_get_term_by_iri_error", iri=iri, error=str(e))
            return None

    def get_service_name(self) -> str:
        """Get the service name.

        Returns:
            'ols'
        """
        return "ols"

    async def is_available(self) -> bool:
        """Check if OLS is available.

        Returns:
            True if OLS is reachable.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/ontologies")
                return response.status_code == 200
        except Exception:
            return False
