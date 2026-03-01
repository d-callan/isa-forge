"""Unit tests for local file parsers."""

import pytest

from isaforge.retrieval.local.csv_parser import CSVParser
from isaforge.retrieval.local.json_parser import JSONParser
from isaforge.retrieval.local.tsv_parser import TSVParser
from isaforge.core.exceptions import RetrievalError


class TestCSVParser:
    """Tests for CSV parser."""

    @pytest.mark.asyncio
    async def test_parse_csv(self, temp_dir, sample_csv_content):
        """Test parsing a CSV file."""
        csv_file = temp_dir / "test.csv"
        csv_file.write_text(sample_csv_content)

        parser = CSVParser()
        result = await parser.parse(str(csv_file))

        assert result["row_count"] == 4
        assert "sample_id" in result["columns"]
        assert "organism" in result["columns"]
        assert len(result["rows"]) == 4

    @pytest.mark.asyncio
    async def test_supports_csv_file(self):
        """Test file type detection."""
        parser = CSVParser()
        assert parser.supports_file("test.csv")
        assert parser.supports_file("data.CSV")
        assert not parser.supports_file("test.tsv")
        assert not parser.supports_file("test.json")

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        parser = CSVParser()
        with pytest.raises(RetrievalError, match="File not found"):
            await parser.parse("/nonexistent/file.csv")

    def test_parser_name(self):
        """Test parser name."""
        parser = CSVParser()
        assert parser.get_parser_name() == "csv"


class TestJSONParser:
    """Tests for JSON parser."""

    @pytest.mark.asyncio
    async def test_parse_json_object(self, temp_dir):
        """Test parsing a JSON object."""
        json_file = temp_dir / "test.json"
        json_file.write_text('{"name": "test", "value": 123}')

        parser = JSONParser()
        result = await parser.parse(str(json_file))

        assert result["data"]["name"] == "test"
        assert result["data"]["value"] == 123

    @pytest.mark.asyncio
    async def test_parse_json_array(self, temp_dir):
        """Test parsing a JSON array."""
        json_file = temp_dir / "test.json"
        json_file.write_text('[{"id": 1}, {"id": 2}]')

        parser = JSONParser()
        result = await parser.parse(str(json_file))

        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_supports_json_file(self):
        """Test file type detection."""
        parser = JSONParser()
        assert parser.supports_file("test.json")
        assert parser.supports_file("data.JSON")
        assert not parser.supports_file("test.csv")

    def test_parser_name(self):
        """Test parser name."""
        parser = JSONParser()
        assert parser.get_parser_name() == "json"


class TestTSVParser:
    """Tests for TSV parser."""

    @pytest.mark.asyncio
    async def test_parse_tsv(self, temp_dir):
        """Test parsing a TSV file."""
        tsv_content = "col1\tcol2\tcol3\nval1\tval2\tval3\n"
        tsv_file = temp_dir / "test.tsv"
        tsv_file.write_text(tsv_content)

        parser = TSVParser()
        result = await parser.parse(str(tsv_file))

        assert result["row_count"] == 1
        assert "col1" in result["columns"]
        assert result["rows"][0]["col1"] == "val1"

    @pytest.mark.asyncio
    async def test_supports_tsv_file(self):
        """Test file type detection."""
        parser = TSVParser()
        assert parser.supports_file("test.tsv")
        assert parser.supports_file("test.txt")
        assert not parser.supports_file("test.csv")

    def test_parser_name(self):
        """Test parser name."""
        parser = TSVParser()
        assert parser.get_parser_name() == "tsv"
