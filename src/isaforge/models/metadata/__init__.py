"""Metadata models for external data sources."""

from isaforge.models.metadata.bioproject import BioProjectMetadata
from isaforge.models.metadata.ontology import OntologyTerm
from isaforge.models.metadata.publication import Publication

__all__ = ["BioProjectMetadata", "Publication", "OntologyTerm"]
