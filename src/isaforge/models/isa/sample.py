"""ISA Sample Pydantic model."""

from pydantic import BaseModel, Field


class Characteristic(BaseModel):
    """A characteristic of a sample or source."""

    category: str = Field(..., description="Characteristic category (e.g., 'organism')")
    value: str = Field(..., description="Characteristic value")
    unit: str | None = Field(default=None, description="Unit of measurement")
    term_accession: str | None = Field(
        default=None, description="Ontology accession for value"
    )
    term_source: str | None = Field(default=None, description="Ontology source for value")
    unit_term_accession: str | None = Field(
        default=None, description="Ontology accession for unit"
    )
    unit_term_source: str | None = Field(
        default=None, description="Ontology source for unit"
    )


class FactorValue(BaseModel):
    """A factor value applied to a sample."""

    factor_name: str = Field(..., description="Name of the study factor")
    value: str = Field(..., description="Factor value")
    unit: str | None = Field(default=None, description="Unit of measurement")
    term_accession: str | None = Field(
        default=None, description="Ontology accession for value"
    )
    term_source: str | None = Field(default=None, description="Ontology source for value")
    unit_term_accession: str | None = Field(
        default=None, description="Ontology accession for unit"
    )
    unit_term_source: str | None = Field(
        default=None, description="Ontology source for unit"
    )


class Source(BaseModel):
    """ISA Source model - the origin material."""

    name: str = Field(..., description="Source name")
    characteristics: list[Characteristic] = Field(
        default_factory=list, description="Source characteristics"
    )


class Sample(BaseModel):
    """ISA Sample model."""

    name: str = Field(..., description="Sample name")
    derives_from: list[str] = Field(
        default_factory=list, description="Source names this sample derives from"
    )
    characteristics: list[Characteristic] = Field(
        default_factory=list, description="Sample characteristics"
    )
    factor_values: list[FactorValue] = Field(
        default_factory=list, description="Factor values for this sample"
    )
