"""JSON file parser for local metadata."""

import json
from pathlib import Path
from typing import Any

import aiofiles

from isaforge.core.exceptions import RetrievalError
from isaforge.observability.logger import get_logger
from isaforge.retrieval.base import BaseLocalParser

logger = get_logger(__name__)


class JSONParser(BaseLocalParser):
    """Parser for JSON metadata files."""

    SUPPORTED_EXTENSIONS = {".json"}

    async def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a JSON file and extract metadata.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Dictionary containing:
                - 'data': The parsed JSON data
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
            async with aiofiles.open(path, encoding="utf-8") as f:
                content = await f.read()

            data = json.loads(content)

            # Determine structure for logging
            if isinstance(data, list):
                structure = f"array with {len(data)} items"
            elif isinstance(data, dict):
                structure = f"object with {len(data)} keys"
            else:
                structure = type(data).__name__

            logger.info(
                "json_parsed",
                file_path=file_path,
                structure=structure,
            )

            return {
                "data": data,
                "source": file_path,
                "parser": self.get_parser_name(),
            }

        except json.JSONDecodeError as e:
            raise RetrievalError(f"JSON parsing error: {e}") from e
        except UnicodeDecodeError as e:
            raise RetrievalError(f"File encoding error: {e}") from e
        except Exception as e:
            raise RetrievalError(f"Failed to parse JSON: {e}") from e

    def supports_file(self, file_path: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the file.

        Returns:
            True if this is a JSON file.
        """
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_parser_name(self) -> str:
        """Get the parser name.

        Returns:
            'json'
        """
        return "json"
