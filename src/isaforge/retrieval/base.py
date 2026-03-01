"""Abstract base class for metadata retrievers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseRetriever(ABC):
    """Abstract base class for metadata retrieval."""

    @abstractmethod
    async def fetch_metadata(self, identifier: str) -> dict[str, Any]:
        """Fetch metadata for a given identifier.

        Args:
            identifier: The identifier to fetch metadata for.

        Returns:
            Dictionary containing the retrieved metadata.

        Raises:
            RetrievalError: If retrieval fails.
        """
        pass

    @abstractmethod
    async def validate_identifier(self, identifier: str) -> bool:
        """Validate that an identifier is properly formatted.

        Args:
            identifier: The identifier to validate.

        Returns:
            True if the identifier is valid, False otherwise.
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this data source.

        Returns:
            Name of the data source (e.g., 'ncbi', 'local_csv').
        """
        pass


class BaseLocalParser(ABC):
    """Abstract base class for local file parsers."""

    @abstractmethod
    async def parse(self, file_path: str) -> dict[str, Any]:
        """Parse a local file and extract metadata.

        Args:
            file_path: Path to the file to parse.

        Returns:
            Dictionary containing the parsed metadata.

        Raises:
            RetrievalError: If parsing fails.
        """
        pass

    @abstractmethod
    def supports_file(self, file_path: str) -> bool:
        """Check if this parser supports the given file.

        Args:
            file_path: Path to the file.

        Returns:
            True if this parser can handle the file.
        """
        pass

    @abstractmethod
    def get_parser_name(self) -> str:
        """Get the name of this parser.

        Returns:
            Name of the parser (e.g., 'csv', 'json').
        """
        pass
