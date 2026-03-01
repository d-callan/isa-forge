"""Publication metadata Pydantic model."""

from datetime import date

from pydantic import BaseModel, Field


class Author(BaseModel):
    """An author of a publication."""

    name: str = Field(..., description="Author name")
    affiliation: str | None = Field(default=None, description="Author affiliation")
    orcid: str | None = Field(default=None, description="ORCID identifier")


class Publication(BaseModel):
    """Publication metadata from PubMed or other sources."""

    pmid: str | None = Field(default=None, description="PubMed ID")
    pmcid: str | None = Field(default=None, description="PubMed Central ID")
    doi: str | None = Field(default=None, description="DOI")
    title: str = Field(..., description="Publication title")
    abstract: str | None = Field(default=None, description="Abstract text")
    authors: list[Author] = Field(default_factory=list, description="List of authors")
    journal: str | None = Field(default=None, description="Journal name")
    publication_date: date | None = Field(default=None, description="Publication date")
    volume: str | None = Field(default=None, description="Journal volume")
    issue: str | None = Field(default=None, description="Journal issue")
    pages: str | None = Field(default=None, description="Page numbers")

    full_text: str | None = Field(
        default=None, description="Full text content if available"
    )
    full_text_source: str | None = Field(
        default=None, description="Source of full text (e.g., 'pmc', 'doi')"
    )

    methods_section: str | None = Field(
        default=None, description="Extracted methods section"
    )
    sample_descriptions: list[str] = Field(
        default_factory=list, description="Extracted sample descriptions"
    )

    keywords: list[str] = Field(default_factory=list, description="Publication keywords")
    mesh_terms: list[str] = Field(default_factory=list, description="MeSH terms")
