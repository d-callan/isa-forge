"""Unit tests for ISA-Tab formatter."""

from isaforge.isa_builder.formatter import ISATabFormatter


class TestISATabFormatter:
    """Test ISATabFormatter class."""

    def test_format_field(self):
        """Test formatting a single field."""
        result = ISATabFormatter.format_field("Study Title", "My Study")
        assert result == "Study Title\tMy Study"

    def test_format_row_single_value(self):
        """Test formatting a row with single value."""
        result = ISATabFormatter.format_row("Study Identifier", "study1")
        assert result == "Study Identifier\tstudy1"

    def test_format_row_multiple_values(self):
        """Test formatting a row with multiple values."""
        result = ISATabFormatter.format_row("Term Source Name", "OBI", "EFO", "NCIT")
        assert result == "Term Source Name\tOBI\tEFO\tNCIT"

    def test_format_row_no_values(self):
        """Test formatting a row with no values."""
        result = ISATabFormatter.format_row("Empty Row")
        assert result == "Empty Row"

    def test_format_header(self):
        """Test formatting a header row."""
        result = ISATabFormatter.format_header("Sample Name", "Organism", "Tissue")
        assert result == "Sample Name\tOrganism\tTissue"

    def test_format_data_row(self):
        """Test formatting a data row."""
        result = ISATabFormatter.format_data_row("sample1", "Homo sapiens", "blood")
        assert result == "sample1\tHomo sapiens\tblood"

    def test_format_data_row_with_none(self):
        """Test formatting a data row with None values."""
        result = ISATabFormatter.format_data_row("sample1", None, "blood")
        assert result == "sample1\t\tblood"

    def test_escape_value_tabs(self):
        """Test escaping tab characters."""
        result = ISATabFormatter.escape_value("value\twith\ttabs")
        assert "\t" not in result
        assert result == "value with tabs"

    def test_escape_value_newlines(self):
        """Test escaping newline characters."""
        result = ISATabFormatter.escape_value("value\nwith\nnewlines")
        assert "\n" not in result
        assert result == "value with newlines"

    def test_escape_value_carriage_return(self):
        """Test escaping carriage return characters."""
        result = ISATabFormatter.escape_value("value\rwith\rreturns")
        assert "\r" not in result

    def test_escape_value_none(self):
        """Test escaping None value."""
        result = ISATabFormatter.escape_value(None)
        assert result == ""

    def test_format_ontology_annotation(self):
        """Test formatting ontology annotation."""
        value, accession, source = ISATabFormatter.format_ontology_annotation(
            "Homo sapiens",
            "NCBITaxon:9606",
            "NCBITAXON",
        )
        assert value == "Homo sapiens"
        assert accession == "NCBITaxon:9606"
        assert source == "NCBITAXON"

    def test_format_ontology_annotation_no_accession(self):
        """Test formatting ontology annotation without accession."""
        value, accession, source = ISATabFormatter.format_ontology_annotation(
            "unknown term",
        )
        assert value == "unknown term"
        assert accession == ""
        assert source == ""

    def test_format_ontology_annotation_escapes_values(self):
        """Test ontology annotation escapes special characters."""
        value, accession, source = ISATabFormatter.format_ontology_annotation(
            "term\twith\ttabs",
            "ACC:123",
            "OBI",
        )
        assert "\t" not in value

    def test_delimiter_constant(self):
        """Test delimiter constant is tab."""
        assert ISATabFormatter.DELIMITER == "\t"
