"""Assay file (a_assay.txt) builder."""

from isaforge.isa_builder.formatter import ISATabFormatter
from isaforge.models.isa import Assay


class AssayBuilder:
    """Builder for a_assay.txt files."""

    def build(self, assay: Assay) -> str:
        """Build assay file content.

        Args:
            assay: The Assay model.

        Returns:
            ISA-Tab formatted assay file content.
        """
        lines = []

        # Build header
        header_columns = self._build_header(assay)
        lines.append(ISATabFormatter.format_header(*header_columns))

        # Build data rows for each process
        for process in assay.processes:
            row = self._build_process_row(assay, process, header_columns)
            lines.append(ISATabFormatter.format_data_row(*row))

        return "\n".join(lines)

    def _build_header(self, assay: Assay) -> list[str]:
        """Build the header row for the assay file.

        Args:
            assay: The Assay model.

        Returns:
            List of column headers.
        """
        columns = ["Sample Name"]

        # Protocol REF
        columns.append("Protocol REF")

        # Add material columns if present
        material_types = set()
        for material in assay.materials:
            material_types.add(material.material_type)

        for material_type in sorted(material_types):
            columns.append(f"{material_type} Name")
            # Add characteristic columns for this material type
            for material in assay.materials:
                if material.material_type == material_type:
                    for char in material.characteristics:
                        columns.append(f"Characteristics[{char.category}]")
                        columns.append("Term Source REF")
                        columns.append("Term Accession Number")
                    break

        # Parameter columns from processes
        param_names = set()
        for process in assay.processes:
            for pv in process.parameter_values:
                param_names.add(pv.parameter_name)

        for param_name in sorted(param_names):
            columns.append(f"Parameter Value[{param_name}]")
            columns.append("Term Source REF")
            columns.append("Term Accession Number")

        # Data file columns
        if assay.data_files:
            columns.append("Raw Data File")

        # Assay name
        columns.append("Assay Name")

        return columns

    def _build_process_row(
        self,
        assay: Assay,
        process,
        header_columns: list[str],
    ) -> list[str]:
        """Build a data row for a process.

        Args:
            assay: The Assay model.
            process: The Process model.
            header_columns: List of column headers.

        Returns:
            List of values for the row.
        """
        row = []

        for col in header_columns:
            if col == "Sample Name":
                # Use first input as sample name
                row.append(process.inputs[0] if process.inputs else "")

            elif col == "Protocol REF":
                row.append(process.protocol_ref)

            elif col.endswith(" Name") and col != "Sample Name" and col != "Assay Name":
                # Material name
                material_type = col[:-5]  # Remove " Name"
                material_name = ""
                for material in assay.materials:
                    if material.material_type == material_type:
                        material_name = material.name
                        break
                row.append(material_name)

            elif col.startswith("Characteristics[") and col.endswith("]"):
                # Already handled with materials
                row.append("")

            elif col == "Term Source REF" or col == "Term Accession Number":
                # Already handled
                continue

            elif col.startswith("Parameter Value[") and col.endswith("]"):
                param_name = col[16:-1]
                value = ""
                for pv in process.parameter_values:
                    if pv.parameter_name == param_name:
                        value = pv.value
                        break
                row.append(value)

            elif col == "Raw Data File":
                # Use first output as data file
                data_file = ""
                for output in process.outputs:
                    for df in assay.data_files:
                        if df.name == output:
                            data_file = df.name
                            break
                    if data_file:
                        break
                row.append(data_file)

            elif col == "Assay Name":
                row.append(process.name or "")

            else:
                row.append("")

        return row
