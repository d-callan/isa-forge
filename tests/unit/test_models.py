"""Unit tests for Pydantic models."""

import pytest

from isaforge.models.isa.investigation import Investigation, OntologySourceReference
from isaforge.models.isa.study import Study, StudyFactor, Person
from isaforge.models.isa.sample import Sample, Source, Characteristic
from isaforge.models.isa.assay import Assay, DataFile
from isaforge.models.isa.protocol import Protocol, ProtocolParameter
from isaforge.models.metadata.bioproject import BioProjectMetadata, SRAExperiment
from isaforge.models.metadata.publication import Publication, Author
from isaforge.models.metadata.ontology import OntologyTerm, OntologyMapping
from isaforge.models.confidence import FieldConfidence, ConfidenceSummary
from isaforge.core.constants import FieldSource, UserAction


class TestISAModels:
    """Tests for ISA-Tab Pydantic models."""

    def test_investigation_creation(self):
        """Test creating an Investigation model."""
        inv = Investigation(
            identifier="INV001",
            title="Test Investigation",
        )
        assert inv.identifier == "INV001"
        assert inv.title == "Test Investigation"
        assert inv.studies == []

    def test_study_creation(self):
        """Test creating a Study model."""
        study = Study(
            identifier="STUDY001",
            title="Test Study",
            filename="s_study.txt",
        )
        assert study.identifier == "STUDY001"
        assert study.filename == "s_study.txt"

    def test_sample_with_characteristics(self):
        """Test creating a Sample with characteristics."""
        sample = Sample(
            name="sample1",
            characteristics=[
                Characteristic(
                    category="organism",
                    value="Homo sapiens",
                    term_accession="NCBITaxon:9606",
                ),
            ],
        )
        assert sample.name == "sample1"
        assert len(sample.characteristics) == 1
        assert sample.characteristics[0].value == "Homo sapiens"

    def test_protocol_with_parameters(self):
        """Test creating a Protocol with parameters."""
        protocol = Protocol(
            name="extraction",
            protocol_type="nucleic acid extraction",
            parameters=[
                ProtocolParameter(name="kit"),
                ProtocolParameter(name="volume"),
            ],
        )
        assert protocol.name == "extraction"
        assert len(protocol.parameters) == 2

    def test_assay_creation(self):
        """Test creating an Assay model."""
        assay = Assay(
            filename="a_assay.txt",
            measurement_type="transcription profiling",
            technology_type="nucleotide sequencing",
        )
        assert assay.filename == "a_assay.txt"
        assert assay.measurement_type == "transcription profiling"


class TestMetadataModels:
    """Tests for metadata Pydantic models."""

    def test_bioproject_metadata(self):
        """Test BioProjectMetadata model."""
        bp = BioProjectMetadata(
            accession="PRJNA123456",
            title="Test Project",
            organism="Homo sapiens",
        )
        assert bp.accession == "PRJNA123456"
        assert bp.organism == "Homo sapiens"

    def test_publication_model(self):
        """Test Publication model."""
        pub = Publication(
            pmid="12345678",
            title="Test Publication",
            authors=[
                Author(name="Smith, John"),
            ],
        )
        assert pub.pmid == "12345678"
        assert len(pub.authors) == 1

    def test_ontology_term(self):
        """Test OntologyTerm model."""
        term = OntologyTerm(
            label="liver",
            term_id="UBERON:0002107",
            ontology="UBERON",
        )
        assert term.label == "liver"
        assert term.term_id == "UBERON:0002107"
        assert not term.is_custom

    def test_ontology_mapping(self):
        """Test OntologyMapping model."""
        term = OntologyTerm(
            label="liver",
            term_id="UBERON:0002107",
            ontology="UBERON",
        )
        mapping = OntologyMapping(
            source_text="liver tissue",
            mapped_term=term,
            confidence=0.95,
            mapping_source="ols",
        )
        assert mapping.source_text == "liver tissue"
        assert mapping.confidence == 0.95


class TestConfidenceModels:
    """Tests for confidence tracking models."""

    def test_field_confidence(self):
        """Test FieldConfidence model."""
        fc = FieldConfidence(
            field_path="study.title",
            value="Test Study",
            confidence=0.95,
            justification="Directly from BioProject metadata",
            source=FieldSource.API_DATA,
        )
        assert fc.field_path == "study.title"
        assert fc.confidence == 0.95
        assert fc.user_action == UserAction.PENDING

    def test_confidence_summary_stats(self):
        """Test ConfidenceSummary statistics calculation."""
        summary = ConfidenceSummary(session_id="test-session")

        summary.fields["field1"] = FieldConfidence(
            field_path="field1",
            value="value1",
            confidence=0.95,
            justification="test",
            source=FieldSource.API_DATA,
            user_action=UserAction.AUTO_ACCEPTED,
        )
        summary.fields["field2"] = FieldConfidence(
            field_path="field2",
            value="value2",
            confidence=0.7,
            justification="test",
            source=FieldSource.LLM_INFERENCE,
            user_action=UserAction.USER_CONFIRMED,
        )

        summary.update_stats()

        assert summary.total_fields == 2
        assert summary.auto_accepted == 1
        assert summary.user_confirmed == 1
        assert summary.average_confidence == pytest.approx(0.825, rel=0.01)
