"""Agent tools for metadata retrieval."""

from typing import Any

from pydantic import BaseModel, Field

from isaforge.observability.logger import get_logger
from isaforge.retrieval.ncbi.bioproject import BioProjectRetriever
from isaforge.retrieval.ncbi.pubmed import PubMedRetriever

logger = get_logger(__name__)


class FetchBioProjectInput(BaseModel):
    """Input for fetching BioProject metadata."""

    bioproject_id: str = Field(..., description="BioProject accession (e.g., PRJNA123456)")


class FetchBioProjectOutput(BaseModel):
    """Output from fetching BioProject metadata."""

    success: bool
    accession: str | None = None
    title: str | None = None
    description: str | None = None
    organism: str | None = None
    linked_pubmed_ids: list[str] = Field(default_factory=list)
    sample_count: int = 0
    experiment_count: int = 0
    error: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)


async def fetch_bioproject_metadata(input_data: FetchBioProjectInput) -> FetchBioProjectOutput:
    """Fetch metadata for a BioProject.

    Args:
        input_data: Input containing the BioProject ID.

    Returns:
        BioProject metadata or error information.
    """
    retriever = BioProjectRetriever()

    try:
        metadata = await retriever.fetch_metadata(input_data.bioproject_id)

        logger.info(
            "bioproject_tool_success",
            bioproject_id=input_data.bioproject_id,
        )

        return FetchBioProjectOutput(
            success=True,
            accession=metadata.get("accession"),
            title=metadata.get("title"),
            description=metadata.get("description"),
            organism=metadata.get("organism"),
            linked_pubmed_ids=metadata.get("linked_pubmed_ids", []),
            sample_count=len(metadata.get("samples", [])),
            experiment_count=len(metadata.get("experiments", [])),
            raw_data=metadata,
        )

    except Exception as e:
        logger.error(
            "bioproject_tool_error",
            bioproject_id=input_data.bioproject_id,
            error=str(e),
        )
        return FetchBioProjectOutput(
            success=False,
            error=str(e),
        )


class FetchPublicationsInput(BaseModel):
    """Input for fetching publications."""

    pmids: list[str] = Field(..., description="List of PubMed IDs to fetch")
    max_count: int = Field(default=6, description="Maximum number to fetch")


class PublicationSummary(BaseModel):
    """Summary of a publication."""

    pmid: str
    title: str
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    doi: str | None = None
    has_full_text: bool = False


class FetchPublicationsOutput(BaseModel):
    """Output from fetching publications."""

    success: bool
    publications: list[PublicationSummary] = Field(default_factory=list)
    error: str | None = None


async def fetch_publications(input_data: FetchPublicationsInput) -> FetchPublicationsOutput:
    """Fetch publication metadata from PubMed.

    Args:
        input_data: Input containing PubMed IDs.

    Returns:
        Publication metadata or error information.
    """
    retriever = PubMedRetriever()

    try:
        publications_data = await retriever.fetch_multiple(
            input_data.pmids,
            max_count=input_data.max_count,
        )

        publications = []
        for pub in publications_data:
            authors = [a.get("name", "") for a in pub.get("authors", [])]
            publications.append(
                PublicationSummary(
                    pmid=pub.get("pmid", ""),
                    title=pub.get("title", ""),
                    abstract=pub.get("abstract"),
                    authors=authors[:5],  # Limit authors
                    journal=pub.get("journal"),
                    doi=pub.get("doi"),
                    has_full_text=pub.get("full_text") is not None,
                )
            )

        logger.info(
            "publications_tool_success",
            count=len(publications),
        )

        return FetchPublicationsOutput(
            success=True,
            publications=publications,
        )

    except Exception as e:
        logger.error("publications_tool_error", error=str(e))
        return FetchPublicationsOutput(
            success=False,
            error=str(e),
        )


class ParseLocalFileInput(BaseModel):
    """Input for parsing a local metadata file."""

    file_path: str = Field(..., description="Path to the local file")


class ParseLocalFileOutput(BaseModel):
    """Output from parsing a local file."""

    success: bool
    file_type: str | None = None
    row_count: int = 0
    columns: list[str] = Field(default_factory=list)
    sample_data: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


async def parse_local_file(input_data: ParseLocalFileInput) -> ParseLocalFileOutput:
    """Parse a local metadata file.

    Args:
        input_data: Input containing the file path.

    Returns:
        Parsed file data or error information.
    """
    from pathlib import Path

    from isaforge.retrieval.local.csv_parser import CSVParser
    from isaforge.retrieval.local.json_parser import JSONParser
    from isaforge.retrieval.local.tsv_parser import TSVParser

    file_path = input_data.file_path
    suffix = Path(file_path).suffix.lower()

    try:
        if suffix == ".csv":
            parser = CSVParser()
        elif suffix == ".json":
            parser = JSONParser()
        elif suffix in {".tsv", ".txt"}:
            parser = TSVParser()
        else:
            return ParseLocalFileOutput(
                success=False,
                error=f"Unsupported file type: {suffix}",
            )

        data = await parser.parse(file_path)

        # Handle different data structures
        if "rows" in data:
            rows = data["rows"]
            columns = data.get("columns", [])
            sample_data = rows[:5]  # First 5 rows as sample
            row_count = len(rows)
        elif "data" in data:
            json_data = data["data"]
            if isinstance(json_data, list):
                row_count = len(json_data)
                sample_data = json_data[:5]
                columns = list(json_data[0].keys()) if json_data and isinstance(json_data[0], dict) else []
            else:
                row_count = 1
                sample_data = [json_data] if isinstance(json_data, dict) else []
                columns = list(json_data.keys()) if isinstance(json_data, dict) else []
        else:
            row_count = 0
            columns = []
            sample_data = []

        logger.info(
            "local_file_tool_success",
            file_path=file_path,
            row_count=row_count,
        )

        return ParseLocalFileOutput(
            success=True,
            file_type=suffix.lstrip("."),
            row_count=row_count,
            columns=columns,
            sample_data=sample_data,
        )

    except Exception as e:
        logger.error("local_file_tool_error", file_path=file_path, error=str(e))
        return ParseLocalFileOutput(
            success=False,
            error=str(e),
        )
