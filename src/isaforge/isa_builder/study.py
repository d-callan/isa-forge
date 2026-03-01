"""Study file (s_study.txt) builder."""

from isaforge.isa_builder.formatter import ISATabFormatter
from isaforge.models.isa import Study


class StudyBuilder:
    """Builder for s_study.txt files."""

    def build(self, study: Study) -> str:
        """Build study file content.

        Args:
            study: The Study model.

        Returns:
            ISA-Tab formatted study file content.
        """
        lines = []

        # Build header
        header_columns = self._build_header(study)
        lines.append(ISATabFormatter.format_header(*header_columns))

        # Build data rows for each sample
        for sample in study.samples:
            row = self._build_sample_row(study, sample, header_columns)
            lines.append(ISATabFormatter.format_data_row(*row))

        return "\n".join(lines)

    def _build_header(self, study: Study) -> list[str]:
        """Build the header row for the study file.

        Args:
            study: The Study model.

        Returns:
            List of column headers.
        """
        columns = ["Source Name"]

        # Add characteristic columns from sources
        characteristic_categories = set()
        for source in study.sources:
            for char in source.characteristics:
                characteristic_categories.add(char.category)

        for category in sorted(characteristic_categories):
            columns.append(f"Characteristics[{category}]")
            columns.append("Term Source REF")
            columns.append("Term Accession Number")

        # Protocol REF
        columns.append("Protocol REF")

        # Sample Name
        columns.append("Sample Name")

        # Add sample characteristic columns
        sample_characteristic_categories = set()
        for sample in study.samples:
            for char in sample.characteristics:
                sample_characteristic_categories.add(char.category)

        for category in sorted(sample_characteristic_categories):
            if category not in characteristic_categories:
                columns.append(f"Characteristics[{category}]")
                columns.append("Term Source REF")
                columns.append("Term Accession Number")

        # Add factor value columns
        factor_names = set()
        for sample in study.samples:
            for fv in sample.factor_values:
                factor_names.add(fv.factor_name)

        for factor_name in sorted(factor_names):
            columns.append(f"Factor Value[{factor_name}]")
            columns.append("Term Source REF")
            columns.append("Term Accession Number")

        return columns

    def _build_sample_row(
        self,
        study: Study,
        sample,
        header_columns: list[str],
    ) -> list[str]:
        """Build a data row for a sample.

        Args:
            study: The Study model.
            sample: The Sample model.
            header_columns: List of column headers.

        Returns:
            List of values for the row.
        """
        row = []

        # Find source for this sample
        source = None
        if sample.derives_from:
            source_name = sample.derives_from[0]
            for s in study.sources:
                if s.name == source_name:
                    source = s
                    break

        for col in header_columns:
            if col == "Source Name":
                row.append(source.name if source else "")

            elif col.startswith("Characteristics[") and col.endswith("]"):
                category = col[16:-1]
                value, term_source, term_accession = self._get_characteristic(
                    source, sample, category
                )
                row.append(value)

            elif col == "Term Source REF":
                # Already handled in characteristics
                continue

            elif col == "Term Accession Number":
                # Already handled in characteristics
                continue

            elif col == "Protocol REF":
                # Use first protocol if available
                if study.protocols:
                    row.append(study.protocols[0].name)
                else:
                    row.append("")

            elif col == "Sample Name":
                row.append(sample.name)

            elif col.startswith("Factor Value[") and col.endswith("]"):
                factor_name = col[13:-1]
                value, term_source, term_accession = self._get_factor_value(
                    sample, factor_name
                )
                row.append(value)

            else:
                row.append("")

        return row

    def _get_characteristic(
        self,
        source,
        sample,
        category: str,
    ) -> tuple[str, str, str]:
        """Get characteristic value for a category.

        Args:
            source: Source model.
            sample: Sample model.
            category: Characteristic category.

        Returns:
            Tuple of (value, term_source, term_accession).
        """
        # Check source first
        if source:
            for char in source.characteristics:
                if char.category == category:
                    return (
                        char.value,
                        char.term_source or "",
                        char.term_accession or "",
                    )

        # Check sample
        for char in sample.characteristics:
            if char.category == category:
                return (
                    char.value,
                    char.term_source or "",
                    char.term_accession or "",
                )

        return ("", "", "")

    def _get_factor_value(
        self,
        sample,
        factor_name: str,
    ) -> tuple[str, str, str]:
        """Get factor value for a factor name.

        Args:
            sample: Sample model.
            factor_name: Factor name.

        Returns:
            Tuple of (value, term_source, term_accession).
        """
        for fv in sample.factor_values:
            if fv.factor_name == factor_name:
                return (
                    fv.value,
                    fv.term_source or "",
                    fv.term_accession or "",
                )

        return ("", "", "")
