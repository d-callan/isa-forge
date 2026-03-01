"""ISA-Tab formatting utilities."""


class ISATabFormatter:
    """Utility class for formatting ISA-Tab content."""

    DELIMITER = "\t"

    @classmethod
    def format_field(cls, name: str, value: str) -> str:
        """Format a single field line.

        Args:
            name: Field name.
            value: Field value.

        Returns:
            Tab-delimited field line.
        """
        return f"{name}{cls.DELIMITER}{value}"

    @classmethod
    def format_row(cls, name: str, *values: str) -> str:
        """Format a row with multiple values.

        Args:
            name: Row name/header.
            *values: Values for the row.

        Returns:
            Tab-delimited row.
        """
        if not values:
            return name
        return f"{name}{cls.DELIMITER}{cls.DELIMITER.join(str(v) for v in values)}"

    @classmethod
    def format_header(cls, *columns: str) -> str:
        """Format a header row.

        Args:
            *columns: Column names.

        Returns:
            Tab-delimited header row.
        """
        return cls.DELIMITER.join(columns)

    @classmethod
    def format_data_row(cls, *values: str) -> str:
        """Format a data row.

        Args:
            *values: Row values.

        Returns:
            Tab-delimited data row.
        """
        return cls.DELIMITER.join(str(v) if v is not None else "" for v in values)

    @classmethod
    def escape_value(cls, value: str) -> str:
        """Escape special characters in a value.

        Args:
            value: Value to escape.

        Returns:
            Escaped value.
        """
        if value is None:
            return ""
        # Escape tabs and newlines
        value = str(value)
        value = value.replace("\t", " ")
        value = value.replace("\n", " ")
        value = value.replace("\r", "")
        return value

    @classmethod
    def format_ontology_annotation(
        cls,
        value: str,
        term_accession: str | None = None,
        term_source: str | None = None,
    ) -> tuple[str, str, str]:
        """Format an ontology-annotated value.

        Args:
            value: The value.
            term_accession: Ontology term accession.
            term_source: Ontology source reference.

        Returns:
            Tuple of (value, term_accession, term_source).
        """
        return (
            cls.escape_value(value),
            cls.escape_value(term_accession or ""),
            cls.escape_value(term_source or ""),
        )
