"""BioProject metadata Pydantic model."""

from datetime import date

from pydantic import BaseModel, Field


class SRAExperiment(BaseModel):
    """SRA Experiment metadata."""

    accession: str = Field(..., description="SRA experiment accession (SRX...)")
    title: str | None = Field(default=None, description="Experiment title")
    library_strategy: str | None = Field(
        default=None, description="Library strategy (e.g., 'RNA-Seq')"
    )
    library_source: str | None = Field(
        default=None, description="Library source (e.g., 'TRANSCRIPTOMIC')"
    )
    library_selection: str | None = Field(
        default=None, description="Library selection (e.g., 'cDNA')"
    )
    library_layout: str | None = Field(
        default=None, description="Library layout (e.g., 'PAIRED')"
    )
    platform: str | None = Field(
        default=None, description="Sequencing platform (e.g., 'ILLUMINA')"
    )
    instrument_model: str | None = Field(
        default=None, description="Instrument model (e.g., 'Illumina HiSeq 2500')"
    )


class SRASample(BaseModel):
    """SRA Sample metadata."""

    accession: str = Field(..., description="SRA sample accession (SRS...)")
    biosample_accession: str | None = Field(
        default=None, description="BioSample accession (SAMN...)"
    )
    title: str | None = Field(default=None, description="Sample title")
    organism: str | None = Field(default=None, description="Organism name")
    taxon_id: int | None = Field(default=None, description="NCBI Taxonomy ID")
    attributes: dict[str, str] = Field(
        default_factory=dict, description="Sample attributes as key-value pairs"
    )


class SRARun(BaseModel):
    """SRA Run metadata."""

    accession: str = Field(..., description="SRA run accession (SRR...)")
    experiment_accession: str = Field(..., description="Parent experiment accession")
    sample_accession: str = Field(..., description="Parent sample accession")
    total_spots: int | None = Field(default=None, description="Total number of spots/reads")
    total_bases: int | None = Field(default=None, description="Total number of bases")
    size: int | None = Field(default=None, description="File size in bytes")


class BioProjectMetadata(BaseModel):
    """BioProject metadata from NCBI."""

    accession: str = Field(..., description="BioProject accession (PRJNA...)")
    title: str | None = Field(default=None, description="Project title")
    description: str | None = Field(default=None, description="Project description")
    organism: str | None = Field(default=None, description="Primary organism")
    taxon_id: int | None = Field(default=None, description="NCBI Taxonomy ID")

    submission_date: date | None = Field(default=None, description="Submission date")
    release_date: date | None = Field(default=None, description="Public release date")
    last_update: date | None = Field(default=None, description="Last update date")

    data_type: str | None = Field(
        default=None, description="Data type (e.g., 'Transcriptome')"
    )
    scope: str | None = Field(
        default=None, description="Project scope (e.g., 'Monoisolate')"
    )

    organization: str | None = Field(
        default=None, description="Submitting organization"
    )
    submitter: str | None = Field(default=None, description="Submitter name")

    linked_pubmed_ids: list[str] = Field(
        default_factory=list, description="Linked PubMed IDs"
    )

    experiments: list[SRAExperiment] = Field(
        default_factory=list, description="SRA experiments"
    )
    samples: list[SRASample] = Field(
        default_factory=list, description="SRA samples"
    )
    runs: list[SRARun] = Field(
        default_factory=list, description="SRA runs"
    )

    raw_metadata: dict = Field(
        default_factory=dict, description="Raw metadata from API"
    )
