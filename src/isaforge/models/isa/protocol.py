"""ISA Protocol Pydantic model."""

from pydantic import BaseModel, Field


class ProtocolParameter(BaseModel):
    """A parameter used in a protocol."""

    name: str = Field(..., description="Parameter name")
    value: str | None = Field(default=None, description="Parameter value")
    unit: str | None = Field(default=None, description="Unit of measurement")
    unit_term_accession: str | None = Field(
        default=None, description="Ontology accession for unit"
    )
    unit_term_source: str | None = Field(
        default=None, description="Ontology source for unit"
    )


class ProtocolComponent(BaseModel):
    """A component used in a protocol (e.g., instrument, software)."""

    name: str = Field(..., description="Component name")
    component_type: str | None = Field(default=None, description="Type of component")
    component_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for component type"
    )
    component_type_term_source: str | None = Field(
        default=None, description="Ontology source for component type"
    )


class Protocol(BaseModel):
    """ISA Protocol model."""

    name: str = Field(..., description="Protocol name")
    protocol_type: str = Field(..., description="Type of protocol")
    protocol_type_term_accession: str | None = Field(
        default=None, description="Ontology accession for protocol type"
    )
    protocol_type_term_source: str | None = Field(
        default=None, description="Ontology source for protocol type"
    )
    description: str | None = Field(default=None, description="Protocol description")
    uri: str | None = Field(default=None, description="URI to protocol document")
    version: str | None = Field(default=None, description="Protocol version")
    parameters: list[ProtocolParameter] = Field(
        default_factory=list, description="Protocol parameters"
    )
    components: list[ProtocolComponent] = Field(
        default_factory=list, description="Protocol components"
    )
