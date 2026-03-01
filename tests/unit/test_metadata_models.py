"""Unit tests for metadata models."""

from isaforge.models.metadata.bioproject import BioProjectMetadata
from isaforge.models.metadata.publication import Publication, Author
from isaforge.models.metadata.ontology import OntologyTerm, OntologyMapping


class TestBioProjectMetadata:
    """Test BioProjectMetadata model."""

    def test_creation(self):
        """Test creating BioProjectMetadata."""
        metadata = BioProjectMetadata(
            accession="PRJNA123456",
            title="Test BioProject",
        )

        assert metadata.accession == "PRJNA123456"
        assert metadata.title == "Test BioProject"

    def test_with_description(self):
        """Test with description."""
        metadata = BioProjectMetadata(
            accession="PRJNA123456",
            title="Test BioProject",
            description="A test project for unit testing",
        )

        assert metadata.description is not None
        assert "test" in metadata.description.lower()

    def test_with_organism(self):
        """Test with organism information."""
        metadata = BioProjectMetadata(
            accession="PRJNA123456",
            title="Test BioProject",
            organism="Homo sapiens",
            taxon_id=9606,
        )

        assert metadata.organism == "Homo sapiens"
        assert metadata.taxon_id == 9606

    def test_defaults(self):
        """Test default values."""
        metadata = BioProjectMetadata(
            accession="PRJNA123456",
            title="Test BioProject",
        )

        assert metadata.description is None
        assert metadata.organism is None


class TestPublication:
    """Test Publication model."""

    def test_creation(self):
        """Test creating Publication."""
        pub = Publication(
            title="Test Publication",
        )

        assert pub.title == "Test Publication"

    def test_with_pmid(self):
        """Test with PMID."""
        pub = Publication(
            pmid="12345678",
            title="Test Publication",
        )

        assert pub.pmid == "12345678"

    def test_with_authors(self):
        """Test with authors."""
        pub = Publication(
            title="Test Publication",
            authors=[
                Author(name="Smith J"),
                Author(name="Doe J"),
            ],
        )

        assert len(pub.authors) == 2

    def test_with_journal(self):
        """Test with journal information."""
        pub = Publication(
            title="Test Publication",
            journal="Nature",
        )

        assert pub.journal == "Nature"

    def test_with_doi(self):
        """Test with DOI."""
        pub = Publication(
            title="Test Publication",
            doi="10.1234/test.2024",
        )

        assert pub.doi == "10.1234/test.2024"

    def test_with_abstract(self):
        """Test with abstract."""
        pub = Publication(
            title="Test Publication",
            abstract="This is a test abstract for the publication.",
        )

        assert pub.abstract is not None
        assert "test" in pub.abstract.lower()

    def test_defaults(self):
        """Test default values."""
        pub = Publication(
            title="Test Publication",
        )

        assert pub.authors == []
        assert pub.journal is None
        assert pub.doi is None


class TestAuthor:
    """Test Author model."""

    def test_creation(self):
        """Test creating Author."""
        author = Author(name="John Smith")
        assert author.name == "John Smith"

    def test_with_affiliation(self):
        """Test with affiliation."""
        author = Author(name="John Smith", affiliation="MIT")
        assert author.affiliation == "MIT"

    def test_with_orcid(self):
        """Test with ORCID."""
        author = Author(name="John Smith", orcid="0000-0001-2345-6789")
        assert author.orcid == "0000-0001-2345-6789"


class TestOntologyTerm:
    """Test OntologyTerm model."""

    def test_creation(self):
        """Test creating OntologyTerm."""
        term = OntologyTerm(
            term_id="OBI:0000070",
            label="assay",
            ontology="OBI",
        )

        assert term.term_id == "OBI:0000070"
        assert term.label == "assay"
        assert term.ontology == "OBI"

    def test_with_description(self):
        """Test with description."""
        term = OntologyTerm(
            term_id="OBI:0000070",
            label="assay",
            ontology="OBI",
            description="A planned process with the objective to produce information.",
        )

        assert term.description is not None

    def test_with_synonyms(self):
        """Test with synonyms."""
        term = OntologyTerm(
            term_id="OBI:0000070",
            label="assay",
            ontology="OBI",
            synonyms=["test", "experiment"],
        )

        assert len(term.synonyms) == 2

    def test_with_iri(self):
        """Test with IRI."""
        term = OntologyTerm(
            term_id="OBI:0000070",
            label="assay",
            ontology="OBI",
            iri="http://purl.obolibrary.org/obo/OBI_0000070",
        )

        assert "obolibrary" in term.iri

    def test_defaults(self):
        """Test default values."""
        term = OntologyTerm(
            term_id="OBI:0000070",
            label="assay",
            ontology="OBI",
        )

        assert term.description is None
        assert term.synonyms == []
        assert term.iri is None


class TestOntologyMapping:
    """Test OntologyMapping model."""

    def test_creation(self):
        """Test creating OntologyMapping."""
        mapping = OntologyMapping(
            source_text="blood sample",
            mapped_term=OntologyTerm(
                term_id="UBERON:0000178",
                label="blood",
                ontology="UBERON",
            ),
            confidence=0.95,
        )

        assert mapping.source_text == "blood sample"
        assert mapping.mapped_term.label == "blood"
        assert mapping.confidence == 0.95

    def test_with_mapping_source(self):
        """Test with mapping source information."""
        mapping = OntologyMapping(
            source_text="blood sample",
            mapped_term=OntologyTerm(
                term_id="UBERON:0000178",
                label="blood",
                ontology="UBERON",
            ),
            confidence=0.95,
            mapping_source="ols",
        )

        assert mapping.mapping_source == "ols"

    def test_with_alternatives(self):
        """Test with alternative mappings."""
        mapping = OntologyMapping(
            source_text="tissue",
            mapped_term=OntologyTerm(
                term_id="UBERON:0000479",
                label="tissue",
                ontology="UBERON",
            ),
            confidence=0.9,
            alternatives=[
                OntologyTerm(
                    term_id="BTO:0001489",
                    label="tissue",
                    ontology="BTO",
                ),
            ],
        )

        assert len(mapping.alternatives) == 1

    def test_defaults(self):
        """Test default values."""
        mapping = OntologyMapping(
            source_text="test",
            mapped_term=OntologyTerm(
                term_id="TEST:001",
                label="test",
                ontology="TEST",
            ),
        )

        assert mapping.mapping_source == "unknown"
        assert mapping.alternatives == []
        assert mapping.confidence == 0.0
