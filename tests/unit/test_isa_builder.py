"""Unit tests for ISA-Tab builder."""

import pytest

from isaforge.isa_builder.builder import ISATabBuilder
from isaforge.isa_builder.formatter import ISATabFormatter


class TestISATabFormatter:
    """Tests for ISA-Tab formatting utilities."""

    def test_format_field(self):
        """Test formatting a single field."""
        result = ISATabFormatter.format_field("Study Title", "Test Study")
        assert result == "Study Title\tTest Study"

    def test_format_row(self):
        """Test formatting a row with multiple values."""
        result = ISATabFormatter.format_row("Author", "Smith", "Jones", "Doe")
        assert result == "Author\tSmith\tJones\tDoe"

    def test_format_row_empty(self):
        """Test formatting a row with no values."""
        result = ISATabFormatter.format_row("Empty Row")
        assert result == "Empty Row"

    def test_format_header(self):
        """Test formatting a header row."""
        result = ISATabFormatter.format_header("Col1", "Col2", "Col3")
        assert result == "Col1\tCol2\tCol3"

    def test_escape_value(self):
        """Test escaping special characters."""
        result = ISATabFormatter.escape_value("Line1\nLine2\tTabbed")
        assert "\n" not in result
        assert "\t" not in result

    def test_escape_none(self):
        """Test escaping None value."""
        result = ISATabFormatter.escape_value(None)
        assert result == ""


class TestISATabBuilder:
    """Tests for ISA-Tab file builder."""

    def test_builder_creates_output_dir(self, temp_dir):
        """Test that builder creates output directory."""
        output_dir = temp_dir / "isa_output"
        builder = ISATabBuilder(output_dir)
        assert output_dir.exists()

    def test_build_investigation(self, temp_dir, sample_investigation_model):
        """Test building ISA-Tab files from Investigation model."""
        builder = ISATabBuilder(temp_dir)
        output_files = builder.build(sample_investigation_model)

        # Check investigation file was created
        assert "investigation" in output_files
        assert output_files["investigation"].exists()

        # Check content
        content = output_files["investigation"].read_text()
        assert "INVESTIGATION" in content
        assert "INV001" in content
        assert "Test Investigation" in content

    def test_build_creates_study_file(self, temp_dir, sample_investigation_model):
        """Test that study file is created."""
        builder = ISATabBuilder(temp_dir)
        output_files = builder.build(sample_investigation_model)

        # Find study file
        study_files = [k for k in output_files if k.startswith("study_")]
        assert len(study_files) == 1

        study_path = output_files[study_files[0]]
        assert study_path.exists()
