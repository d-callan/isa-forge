"""ISA Investigation Pydantic model."""

from pydantic import BaseModel, Field

from isaforge.models.isa.study import Person, Study


class OntologySourceReference(BaseModel):
    """Reference to an ontology source used in the investigation."""

    name: str = Field(..., description="Ontology name (e.g., 'OBI')")
    file: str | None = Field(default=None, description="Ontology file location")
    version: str | None = Field(default=None, description="Ontology version")
    description: str | None = Field(default=None, description="Ontology description")


class InvestigationPublication(BaseModel):
    """A publication associated with the investigation."""

    pubmed_id: str | None = Field(default=None, description="PubMed ID")
    doi: str | None = Field(default=None, description="DOI")
    author_list: str | None = Field(default=None, description="List of authors")
    title: str | None = Field(default=None, description="Publication title")
    status: str | None = Field(default=None, description="Publication status")
    status_term_accession: str | None = Field(
        default=None, description="Ontology accession for status"
    )
    status_term_source: str | None = Field(
        default=None, description="Ontology source for status"
    )


class Investigation(BaseModel):
    """ISA Investigation model - the top-level container."""

    identifier: str = Field(..., description="Investigation identifier")
    title: str = Field(..., description="Investigation title")
    description: str | None = Field(default=None, description="Investigation description")
    submission_date: str | None = Field(default=None, description="Submission date")
    public_release_date: str | None = Field(default=None, description="Public release date")

    ontology_source_references: list[OntologySourceReference] = Field(
        default_factory=list, description="Ontology sources used"
    )
    publications: list[InvestigationPublication] = Field(
        default_factory=list, description="Publications associated with the investigation"
    )
    contacts: list[Person] = Field(
        default_factory=list, description="People involved in the investigation"
    )
    studies: list[Study] = Field(
        default_factory=list, description="Studies in the investigation"
    )

    comments: dict[str, str] = Field(
        default_factory=dict, description="Investigation-level comments"
    )
