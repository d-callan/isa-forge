"""ISA Assay Pydantic model."""

from pydantic import BaseModel, Field

from isaforge.models.isa.sample import Characteristic


class DataFile(BaseModel):
    """A data file produced by an assay."""

    name: str = Field(..., description="Data file name")
    file_type: str | None = Field(default=None, description="Type of data file")
    comments: dict[str, str] = Field(
        default_factory=dict, description="Comments on the data file"
    )


class ProcessParameterValue(BaseModel):
    """A parameter value for a process execution."""

    parameter_name: str = Field(..., description="Name of the protocol parameter")
    value: str = Field(..., description="Parameter value")
    unit: str | None = Field(default=None, description="Unit of measurement")
    term_accession: str | None = Field(
        default=None, description="Ontology accession for value"
    )
    term_source: str | None = Field(default=None, description="Ontology source for value")


class Process(BaseModel):
    """A process in the assay workflow."""

    name: str | None = Field(default=None, description="Process name")
    protocol_ref: str = Field(..., description="Reference to protocol name")
    performer: str | None = Field(default=None, description="Person who performed the process")
    date: str | None = Field(default=None, description="Date of process execution")
    parameter_values: list[ProcessParameterValue] = Field(
        default_factory=list, description="Parameter values for this process"
    )
    inputs: list[str] = Field(
        default_factory=list, description="Input sample/material names"
    )
    outputs: list[str] = Field(
        default_factory=list, description="Output sample/material/data names"
    )


class AssayMaterial(BaseModel):
    """Material used or produced in an assay (e.g., Extract, Labeled Extract)."""

    name: str = Field(..., description="Material name")
    material_type: str = Field(..., description="Type of material")
    characteristics: list[Characteristic] = Field(
        default_factory=list, description="Material characteristics"
    )


class Assay(BaseModel):
    """ISA Assay model."""

    filename: str = Field(..., description="Assay file name (e.g., 'a_assay.txt')")
    measurement_type: str = Field(..., description="Type of measurement")
    measurement_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for measurement type"
    )
    measurement_type_term_source: str | None = Field(
        default=None, description="Ontology source for measurement type"
    )
    technology_type: str = Field(..., description="Technology used")
    technology_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for technology type"
    )
    technology_type_term_source: str | None = Field(
        default=None, description="Ontology source for technology type"
    )
    technology_platform: str | None = Field(
        default=None, description="Technology platform (e.g., 'Illumina')"
    )
    materials: list[AssayMaterial] = Field(
        default_factory=list, description="Materials in the assay"
    )
    data_files: list[DataFile] = Field(
        default_factory=list, description="Data files produced"
    )
    processes: list[Process] = Field(
        default_factory=list, description="Processes in the assay workflow"
    )
    comments: dict[str, str] = Field(
        default_factory=dict, description="Assay-level comments"
    )
