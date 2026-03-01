"""NCBI Entrez API client."""

from typing import Any
from urllib.parse import urlencode

import httpx

from isaforge.core.config import settings
from isaforge.core.constants import (
    NCBI_EFETCH,
    NCBI_ELINK,
    NCBI_ESEARCH,
    NCBI_ESUMMARY,
)
from isaforge.core.exceptions import NCBIError
from isaforge.observability.circuit_breaker import CircuitBreakerRegistry
from isaforge.observability.logger import get_logger
from isaforge.observability.metrics import Timer

logger = get_logger(__name__)

# Circuit breaker for NCBI API
ncbi_circuit_breaker = CircuitBreakerRegistry.get_or_create(
    "ncbi_api",
    max_failures=5,
    timeout_seconds=120.0,
)


class NCBIClient:
    """Async client for NCBI Entrez APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the NCBI client.

        Args:
            api_key: NCBI API key for higher rate limits.
            email: Email for NCBI API identification.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or settings.ncbi_api_key
        self.email = email or settings.ncbi_email
        self.timeout = timeout

    def _build_params(self, **kwargs: Any) -> dict[str, Any]:
        """Build request parameters with common fields.

        Args:
            **kwargs: Additional parameters.

        Returns:
            Dictionary of parameters.
        """
        params = {"retmode": "json", **kwargs}
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email
        return params

    async def _request(
        self,
        url: str,
        params: dict[str, Any],
        operation: str,
    ) -> dict[str, Any]:
        """Make an async HTTP request to NCBI.

        Args:
            url: The API endpoint URL.
            params: Query parameters.
            operation: Name of the operation for logging.

        Returns:
            JSON response as dictionary.

        Raises:
            NCBIError: If the request fails.
        """
        async def _do_request() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with Timer(f"ncbi_{operation}", {"url": url}):
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

        try:
            return await ncbi_circuit_breaker.call_async(_do_request)
        except httpx.HTTPStatusError as e:
            logger.error(
                "ncbi_http_error",
                operation=operation,
                status_code=e.response.status_code,
                url=str(e.request.url),
            )
            raise NCBIError(f"NCBI API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("ncbi_request_error", operation=operation, error=str(e))
            raise NCBIError(f"NCBI request failed: {e}") from e

    async def esearch(
        self,
        db: str,
        term: str,
        retmax: int = 100,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Search an NCBI database.

        Args:
            db: Database name (e.g., 'bioproject', 'pubmed', 'sra').
            term: Search term.
            retmax: Maximum number of results.
            **kwargs: Additional parameters.

        Returns:
            Search results.
        """
        params = self._build_params(db=db, term=term, retmax=retmax, **kwargs)
        result = await self._request(NCBI_ESEARCH, params, f"esearch_{db}")
        return result.get("esearchresult", {})

    async def efetch(
        self,
        db: str,
        ids: list[str],
        rettype: str = "xml",
        **kwargs: Any,
    ) -> dict[str, Any] | str:
        """Fetch records from an NCBI database.

        Args:
            db: Database name.
            ids: List of IDs to fetch.
            rettype: Return type ('xml', 'json', etc.).
            **kwargs: Additional parameters.

        Returns:
            Fetched records.
        """
        params = self._build_params(
            db=db,
            id=",".join(ids),
            rettype=rettype,
            **kwargs,
        )
        # efetch may return XML, so handle differently
        if rettype == "xml":
            params["retmode"] = "xml"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(NCBI_EFETCH, params=params)
                response.raise_for_status()
                return response.text
        return await self._request(NCBI_EFETCH, params, f"efetch_{db}")

    async def esummary(
        self,
        db: str,
        ids: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Get document summaries from an NCBI database.

        Args:
            db: Database name.
            ids: List of IDs to summarize.
            **kwargs: Additional parameters.

        Returns:
            Document summaries.
        """
        params = self._build_params(db=db, id=",".join(ids), **kwargs)
        result = await self._request(NCBI_ESUMMARY, params, f"esummary_{db}")
        return result.get("result", {})

    async def elink(
        self,
        dbfrom: str,
        db: str,
        ids: list[str],
        linkname: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Find related records in NCBI databases.

        Args:
            dbfrom: Source database.
            db: Target database.
            ids: List of IDs from source database.
            linkname: Specific link name (e.g., 'bioproject_pubmed').
            **kwargs: Additional parameters.

        Returns:
            Linked records.
        """
        params = self._build_params(
            dbfrom=dbfrom,
            db=db,
            id=",".join(ids),
            **kwargs,
        )
        if linkname:
            params["linkname"] = linkname
        result = await self._request(NCBI_ELINK, params, f"elink_{dbfrom}_{db}")
        return result.get("linksets", [])

    async def search_bioproject(self, accession: str) -> dict[str, Any]:
        """Search for a BioProject by accession.

        Args:
            accession: BioProject accession (e.g., 'PRJNA123456').

        Returns:
            Search results with BioProject ID.
        """
        return await self.esearch("bioproject", accession)

    async def get_bioproject_summary(self, bioproject_id: str) -> dict[str, Any]:
        """Get summary for a BioProject.

        Args:
            bioproject_id: BioProject UID.

        Returns:
            BioProject summary.
        """
        return await self.esummary("bioproject", [bioproject_id])

    async def get_linked_pubmed(self, bioproject_id: str) -> list[str]:
        """Get PubMed IDs linked to a BioProject.

        Args:
            bioproject_id: BioProject UID.

        Returns:
            List of linked PubMed IDs.
        """
        linksets = await self.elink(
            dbfrom="bioproject",
            db="pubmed",
            ids=[bioproject_id],
            linkname="bioproject_pubmed",
        )

        pmids = []
        for linkset in linksets:
            for linksetdb in linkset.get("linksetdbs", []):
                if linksetdb.get("dbto") == "pubmed":
                    pmids.extend(str(link["id"]) for link in linksetdb.get("links", []))

        return pmids

    async def get_linked_sra(self, bioproject_id: str) -> list[str]:
        """Get SRA IDs linked to a BioProject.

        Args:
            bioproject_id: BioProject UID.

        Returns:
            List of linked SRA IDs.
        """
        linksets = await self.elink(
            dbfrom="bioproject",
            db="sra",
            ids=[bioproject_id],
            linkname="bioproject_sra",
        )

        sra_ids = []
        for linkset in linksets:
            for linksetdb in linkset.get("linksetdbs", []):
                if linksetdb.get("dbto") == "sra":
                    sra_ids.extend(str(link["id"]) for link in linksetdb.get("links", []))

        return sra_ids
