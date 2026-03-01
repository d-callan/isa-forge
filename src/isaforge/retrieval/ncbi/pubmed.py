"""PubMed metadata retrieval from NCBI."""

import re
import xml.etree.ElementTree as ET
from datetime import date
from typing import Any

from isaforge.core.config import settings
from isaforge.core.exceptions import NCBIError, PublicationError, RetrievalError
from isaforge.models.metadata.publication import Author, Publication
from isaforge.observability.logger import get_logger
from isaforge.retrieval.base import BaseRetriever
from isaforge.retrieval.ncbi.client import NCBIClient

logger = get_logger(__name__)

# Regex patterns
PMID_PATTERN = re.compile(r"^\d+$")
PMCID_PATTERN = re.compile(r"^PMC\d+$")


class PubMedRetriever(BaseRetriever):
    """Retriever for PubMed publication metadata."""

    def __init__(self, client: NCBIClient | None = None):
        """Initialize the retriever.

        Args:
            client: Optional NCBI client instance.
        """
        self.client = client or NCBIClient()

    async def validate_identifier(self, identifier: str) -> bool:
        """Validate a PubMed ID.

        Args:
            identifier: The PMID to validate.

        Returns:
            True if valid PMID format.
        """
        return bool(PMID_PATTERN.match(identifier))

    def get_source_name(self) -> str:
        """Get the source name.

        Returns:
            'ncbi_pubmed'
        """
        return "ncbi_pubmed"

    async def fetch_metadata(self, identifier: str) -> dict[str, Any]:
        """Fetch PubMed article metadata.

        Args:
            identifier: PubMed ID.

        Returns:
            Dictionary with publication metadata.

        Raises:
            RetrievalError: If retrieval fails.
        """
        pmid = identifier.strip()

        if not await self.validate_identifier(pmid):
            raise RetrievalError(f"Invalid PubMed ID: {identifier}")

        try:
            # Fetch article XML
            xml_content = await self.client.efetch(
                db="pubmed",
                ids=[pmid],
                rettype="xml",
            )

            if not isinstance(xml_content, str):
                raise RetrievalError(f"Unexpected response for PMID {pmid}")

            metadata = self._parse_pubmed_xml(xml_content, pmid)

            logger.info(
                "pubmed_fetched",
                pmid=pmid,
                title=metadata.get("title", "")[:50],
            )

            return metadata

        except NCBIError:
            raise
        except Exception as e:
            raise RetrievalError(f"Failed to fetch PubMed article: {e}") from e

    def _parse_pubmed_xml(self, xml_content: str, pmid: str) -> dict[str, Any]:
        """Parse PubMed XML response.

        Args:
            xml_content: XML string from NCBI.
            pmid: The PubMed ID.

        Returns:
            Parsed publication metadata.
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise PublicationError(f"Failed to parse PubMed XML: {e}") from e

        article = root.find(".//PubmedArticle")
        if article is None:
            raise PublicationError(f"No article found for PMID {pmid}")

        medline = article.find("MedlineCitation")
        article_elem = medline.find("Article") if medline else None

        if article_elem is None:
            raise PublicationError(f"No article data for PMID {pmid}")

        # Parse basic metadata
        title = article_elem.findtext("ArticleTitle", "")
        abstract_elem = article_elem.find("Abstract")
        abstract = ""
        if abstract_elem is not None:
            abstract_parts = []
            for text_elem in abstract_elem.findall("AbstractText"):
                label = text_elem.get("Label", "")
                text = text_elem.text or ""
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts)

        # Parse authors
        authors = []
        author_list = article_elem.find("AuthorList")
        if author_list is not None:
            for author_elem in author_list.findall("Author"):
                last_name = author_elem.findtext("LastName", "")
                first_name = author_elem.findtext("ForeName", "")
                initials = author_elem.findtext("Initials", "")

                name = f"{last_name}, {first_name}" if first_name else last_name
                if not name and initials:
                    name = initials

                affiliation = ""
                aff_elem = author_elem.find("AffiliationInfo/Affiliation")
                if aff_elem is not None:
                    affiliation = aff_elem.text or ""

                if name:
                    authors.append({
                        "name": name,
                        "affiliation": affiliation or None,
                        "orcid": None,
                    })

        # Parse journal info
        journal_elem = article_elem.find("Journal")
        journal = ""
        volume = ""
        issue = ""
        pub_date = None

        if journal_elem is not None:
            journal = journal_elem.findtext("Title", "")
            ji = journal_elem.find("JournalIssue")
            if ji is not None:
                volume = ji.findtext("Volume", "")
                issue = ji.findtext("Issue", "")

                # Parse date
                pub_date_elem = ji.find("PubDate")
                if pub_date_elem is not None:
                    year = pub_date_elem.findtext("Year")
                    month = pub_date_elem.findtext("Month", "01")
                    day = pub_date_elem.findtext("Day", "01")
                    if year:
                        # Convert month name to number if needed
                        month_map = {
                            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
                        }
                        month = month_map.get(month, month)
                        try:
                            pub_date = date(int(year), int(month), int(day))
                        except (ValueError, TypeError):
                            try:
                                pub_date = date(int(year), 1, 1)
                            except (ValueError, TypeError):
                                pass

        # Parse pagination
        pages = article_elem.findtext("Pagination/MedlinePgn", "")

        # Parse DOI and PMC ID
        doi = None
        pmcid = None
        article_id_list = article.find("PubmedData/ArticleIdList")
        if article_id_list is not None:
            for aid in article_id_list.findall("ArticleId"):
                id_type = aid.get("IdType", "")
                if id_type == "doi":
                    doi = aid.text
                elif id_type == "pmc":
                    pmcid = aid.text

        # Parse MeSH terms
        mesh_terms = []
        mesh_list = medline.find("MeshHeadingList") if medline else None
        if mesh_list is not None:
            for mesh in mesh_list.findall("MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)

        # Parse keywords
        keywords = []
        keyword_list = medline.find("KeywordList") if medline else None
        if keyword_list is not None:
            for kw in keyword_list.findall("Keyword"):
                if kw.text:
                    keywords.append(kw.text)

        return {
            "pmid": pmid,
            "pmcid": pmcid,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "publication_date": pub_date,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "keywords": keywords,
            "mesh_terms": mesh_terms,
            "full_text": None,
            "full_text_source": None,
            "methods_section": None,
            "sample_descriptions": [],
        }

    async def fetch_multiple(
        self,
        pmids: list[str],
        max_count: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch multiple PubMed articles.

        Args:
            pmids: List of PubMed IDs.
            max_count: Maximum number to fetch (defaults to settings.max_publications).

        Returns:
            List of publication metadata dictionaries.
        """
        max_count = max_count or settings.max_publications
        pmids_to_fetch = pmids[:max_count]

        publications = []
        for pmid in pmids_to_fetch:
            try:
                pub = await self.fetch_metadata(pmid)
                publications.append(pub)
            except Exception as e:
                logger.warning("pubmed_fetch_failed", pmid=pmid, error=str(e))

        return publications

    async def to_pydantic(self, identifier: str) -> Publication:
        """Fetch and return as Pydantic model.

        Args:
            identifier: PubMed ID.

        Returns:
            Publication model.
        """
        data = await self.fetch_metadata(identifier)

        return Publication(
            pmid=data.get("pmid"),
            pmcid=data.get("pmcid"),
            doi=data.get("doi"),
            title=data["title"],
            abstract=data.get("abstract"),
            authors=[Author(**a) for a in data.get("authors", [])],
            journal=data.get("journal"),
            publication_date=data.get("publication_date"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            pages=data.get("pages"),
            full_text=data.get("full_text"),
            full_text_source=data.get("full_text_source"),
            methods_section=data.get("methods_section"),
            sample_descriptions=data.get("sample_descriptions", []),
            keywords=data.get("keywords", []),
            mesh_terms=data.get("mesh_terms", []),
        )

    async def to_pydantic_list(
        self,
        pmids: list[str],
        max_count: int | None = None,
    ) -> list[Publication]:
        """Fetch multiple and return as Pydantic models.

        Args:
            pmids: List of PubMed IDs.
            max_count: Maximum number to fetch.

        Returns:
            List of Publication models.
        """
        data_list = await self.fetch_multiple(pmids, max_count)
        publications = []

        for data in data_list:
            try:
                pub = Publication(
                    pmid=data.get("pmid"),
                    pmcid=data.get("pmcid"),
                    doi=data.get("doi"),
                    title=data["title"],
                    abstract=data.get("abstract"),
                    authors=[Author(**a) for a in data.get("authors", [])],
                    journal=data.get("journal"),
                    publication_date=data.get("publication_date"),
                    volume=data.get("volume"),
                    issue=data.get("issue"),
                    pages=data.get("pages"),
                    full_text=data.get("full_text"),
                    full_text_source=data.get("full_text_source"),
                    methods_section=data.get("methods_section"),
                    sample_descriptions=data.get("sample_descriptions", []),
                    keywords=data.get("keywords", []),
                    mesh_terms=data.get("mesh_terms", []),
                )
                publications.append(pub)
            except Exception as e:
                logger.warning("publication_model_error", error=str(e))

        return publications
