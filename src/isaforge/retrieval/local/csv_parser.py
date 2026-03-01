"""CSV file parser for local metadata."""

import csv
from pathlib import Path
from typing import Any

import aiofiles

from isaforge.core.exceptions import RetrievalError
from isaforge.observability.logger import get_logger
from isaforge.retrieval.base import BaseLocalParser

logger = get_logger(__name__)


class CSVParser(BaseLocalParser):
    """Parser for CSV metadata files."""

    SUPPORTED_EXTENSIONS = {".csv"}

    async def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a CSV file and extract metadata.

        Args:
            file_path: Path to the CSV file.

        Returns:
            Dictionary containing:
                - 'rows': List of dictionaries (one per row)
                - 'columns': List of column names
                - 'row_count': Number of data rows
                - 'source': File path

        Raises:
            RetrievalError: If parsing fails.
        """
        path = Path(file_path)

        if not path.exists():
            raise RetrievalError(f"File not found: {file_path}")

        if not self.supports_file(file_path):
            raise RetrievalError(f"Unsupported file type: {path.suffix}")

        try:
            async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
                content = await f.read()

            # Parse CSV content
            reader = csv.DictReader(content.splitlines())
            rows = list(reader)
            columns = reader.fieldnames or []

            logger.info(
                "csv_parsed",
                file_path=file_path,
                row_count=len(rows),
                column_count=len(columns),
            )

            return {
                "rows": rows,
                "columns": columns,
                "row_count": len(rows),
                "source": file_path,
                "parser": self.get_parser_name(),
            }

        except csv.Error as e:
            raise RetrievalError(f"CSV parsing error: {e}") from e
        except UnicodeDecodeError as e:
            raise RetrievalError(f"File encoding error: {e}") from e
        except Exception as e:
            raise RetrievalError(f"Failed to parse CSV: {e}") from e

    def supports_file(self, file_path: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the file.

        Returns:
            True if this is a CSV file.
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_parser_name(self) -> str:
        """Get the parser name.

        Returns:
            'csv'
        """
        return "csv"
