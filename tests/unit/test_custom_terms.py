"""Unit tests for custom term management."""

from isaforge.ontology.custom_terms import (
    CustomTermDefinition,
    DataDictionary,
)
from isaforge.models.metadata.ontology import OntologyTerm


class TestCustomTermDefinition:
    """Test CustomTermDefinition model."""

    def test_creation(self):
        """Test creating a CustomTermDefinition."""
        term = CustomTermDefinition(
            term_id="ISAFORGE:000001",
            label="custom tissue type",
            source_text="custom tissue",
        )

        assert term.term_id == "ISAFORGE:000001"
        assert term.label == "custom tissue type"
        assert term.source_text == "custom tissue"

    def test_with_definition(self):
        """Test with definition."""
        term = CustomTermDefinition(
            term_id="ISAFORGE:000002",
            label="novel assay type",
            source_text="novel assay",
            definition="A custom assay type not found in standard ontologies",
        )

        assert term.definition is not None
        assert "custom assay" in term.definition

    def test_with_context(self):
        """Test with context."""
        term = CustomTermDefinition(
            term_id="ISAFORGE:000003",
            label="experimental condition",
            source_text="special condition",
            context="Used in study design section",
        )

        assert term.context == "Used in study design section"

    def test_with_suggested_ontologies(self):
        """Test with suggested ontologies."""
        term = CustomTermDefinition(
            term_id="ISAFORGE:000004",
            label="cell type",
            source_text="specialized cell",
            suggested_ontologies=["CL", "UBERON"],
        )

        assert len(term.suggested_ontologies) == 2
        assert "CL" in term.suggested_ontologies

    def test_defaults(self):
        """Test default values."""
        term = CustomTermDefinition(
            term_id="ISAFORGE:000005",
            label="test term",
            source_text="test",
        )

        assert term.definition is None
        assert term.context is None
        assert term.suggested_ontologies == []
        assert term.created_by == "isaforge"
        assert term.created_at is not None


class TestDataDictionary:
    """Test DataDictionary model."""

    def test_creation(self):
        """Test creating a DataDictionary."""
        dictionary = DataDictionary(session_id="test-session")

        assert dictionary.session_id == "test-session"
        assert dictionary.terms == {}
        assert dictionary.created_at is not None

    def test_add_term(self):
        """Test adding a term to the dictionary."""
        dictionary = DataDictionary(session_id="test-session")

        # Create an OntologyTerm to add
        ont_term = OntologyTerm(
            term_id="ISAFORGE:000001",
            label="custom term",
            ontology="ISAFORGE",
        )

        term_def = dictionary.add_term(
            term=ont_term,
            source_text="original text",
            definition="A custom term definition",
        )

        assert term_def.term_id == "ISAFORGE:000001"
        assert "ISAFORGE:000001" in dictionary.terms

    def test_add_multiple_terms(self):
        """Test adding multiple terms."""
        dictionary = DataDictionary(session_id="test-session")

        for i in range(3):
            ont_term = OntologyTerm(
                term_id=f"ISAFORGE:00000{i}",
                label=f"term {i}",
                ontology="ISAFORGE",
            )
            dictionary.add_term(term=ont_term, source_text=f"source {i}")

        assert len(dictionary.terms) == 3

    def test_to_dict(self):
        """Test converting to dictionary."""
        dictionary = DataDictionary(session_id="test-session")

        ont_term = OntologyTerm(
            term_id="ISAFORGE:000001",
            label="test term",
            ontology="ISAFORGE",
        )
        dictionary.add_term(term=ont_term, source_text="test source")

        result = dictionary.to_dict()

        assert "session_id" in result
        assert "terms" in result
        assert result["session_id"] == "test-session"

    def test_get_term(self):
        """Test getting a term by ID."""
        dictionary = DataDictionary(session_id="test-session")

        ont_term = OntologyTerm(
            term_id="ISAFORGE:000001",
            label="test term",
            ontology="ISAFORGE",
        )
        dictionary.add_term(term=ont_term, source_text="test source")

        term = dictionary.get_term("ISAFORGE:000001")
        assert term is not None
        assert term.label == "test term"

    def test_get_nonexistent_term(self):
        """Test getting a nonexistent term."""
        dictionary = DataDictionary(session_id="test-session")

        term = dictionary.get_term("NONEXISTENT:000001")
        assert term is None
