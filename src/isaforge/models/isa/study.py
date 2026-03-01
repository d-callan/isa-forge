"""ISA Study Pydantic model."""

from pydantic import BaseModel, Field

from isaforge.models.isa.assay import Assay
from isaforge.models.isa.protocol import Protocol
from isaforge.models.isa.sample import Sample, Source


class StudyFactor(BaseModel):
    """A factor in the study design."""

    name: str = Field(..., description="Factor name")
    factor_type: str = Field(..., description="Type of factor")
    factor_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for factor type"
    )
    factor_type_term_source: str | None = Field(
        default=None, description="Ontology source for factor type"
    )


class StudyDesignDescriptor(BaseModel):
    """A descriptor of the study design."""

    design_type: str = Field(..., description="Type of study design")
    design_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for design type"
    )
    design_type_term_source: str | None = Field(
        default=None, description="Ontology source for design type"
    )


class Person(BaseModel):
    """A person involved in the study."""

    last_name: str = Field(..., description="Last name")
    first_name: str | None = Field(default=None, description="First name")
    mid_initials: str | None = Field(default=None, description="Middle initials")
    email: str | None = Field(default=None, description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    fax: str | None = Field(default=None, description="Fax number")
    address: str | None = Field(default=None, description="Address")
    affiliation: str | None = Field(default=None, description="Affiliation")
    roles: list[str] = Field(default_factory=list, description="Roles in the study")
    roles_term_accessions: list[str] = Field(
        default_factory=list, description="Ontology accessions for roles"
    )
    roles_term_sources: list[str] = Field(
        default_factory=list, description="Ontology sources for roles"
    )


class StudyPublication(BaseModel):
    """A publication associated with the study."""

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


class Study(BaseModel):
    """ISA Study model."""

    identifier: str = Field(..., description="Study identifier")
    title: str = Field(..., description="Study title")
    description: str | None = Field(default=None, description="Study description")
    submission_date: str | None = Field(default=None, description="Submission date")
    public_release_date: str | None = Field(default=None, description="Public release date")
    filename: str = Field(..., description="Study file name (e.g., 's_study.txt')")

    design_descriptors: list[StudyDesignDescriptor] = Field(
        default_factory=list, description="Study design descriptors"
    )
    factors: list[StudyFactor] = Field(
        default_factory=list, description="Study factors"
    )
    protocols: list[Protocol] = Field(
        default_factory=list, description="Protocols used in the study"
    )
    contacts: list[Person] = Field(
        default_factory=list, description="People involved in the study"
    )
    publications: list[StudyPublication] = Field(
        default_factory=list, description="Publications associated with the study"
    )

    sources: list[Source] = Field(
        default_factory=list, description="Source materials"
    )
    samples: list[Sample] = Field(
        default_factory=list, description="Samples in the study"
    )
    assays: list[Assay] = Field(
        default_factory=list, description="Assays in the study"
    )

    comments: dict[str, str] = Field(
        default_factory=dict, description="Study-level comments"
    )
