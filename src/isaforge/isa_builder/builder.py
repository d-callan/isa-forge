"""Main ISA-Tab builder that coordinates file generation."""

from pathlib import Path
from typing import Any

from isaforge.core.constants import (
    ISA_ASSAY_FILE_PREFIX,
    ISA_INVESTIGATION_FILE,
    ISA_STUDY_FILE_PREFIX,
)
from isaforge.isa_builder.investigation import InvestigationBuilder
from isaforge.isa_builder.study import StudyBuilder
from isaforge.isa_builder.assay import AssayBuilder
from isaforge.models.isa import Investigation
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class ISATabBuilder:
    """Builder for generating ISA-Tab files from Pydantic models."""

    def __init__(self, output_dir: str | Path):
        """Initialize the builder.

        Args:
            output_dir: Directory to write ISA-Tab files to.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.investigation_builder = InvestigationBuilder()
        self.study_builder = StudyBuilder()
        self.assay_builder = AssayBuilder()

    def build(self, investigation: Investigation) -> dict[str, Path]:
        """Build ISA-Tab files from an Investigation model.

        Args:
            investigation: The Investigation model to build from.

        Returns:
            Dictionary mapping file type to output path.
        """
        output_files = {}

        # Build investigation file
        investigation_path = self.output_dir / ISA_INVESTIGATION_FILE
        investigation_content = self.investigation_builder.build(investigation)
        investigation_path.write_text(investigation_content, encoding="utf-8")
        output_files["investigation"] = investigation_path

        logger.info("investigation_file_written", path=str(investigation_path))

        # Build study and assay files for each study
        for study in investigation.studies:
            # Build study file
            study_filename = f"{ISA_STUDY_FILE_PREFIX}{study.identifier}.txt"
            study_path = self.output_dir / study_filename
            study_content = self.study_builder.build(study)
            study_path.write_text(study_content, encoding="utf-8")
            output_files[f"study_{study.identifier}"] = study_path

            logger.info("study_file_written", path=str(study_path))

            # Build assay files
            for assay in study.assays:
                assay_path = self.output_dir / assay.filename
                assay_content = self.assay_builder.build(assay)
                assay_path.write_text(assay_content, encoding="utf-8")
                output_files[f"assay_{assay.filename}"] = assay_path

                logger.info("assay_file_written", path=str(assay_path))

        return output_files

    def build_from_dict(self, data: dict[str, Any]) -> dict[str, Path]:
        """Build ISA-Tab files from a dictionary.

        Args:
            data: Dictionary representation of an Investigation.

        Returns:
            Dictionary mapping file type to output path.
        """
        investigation = Investigation(**data)
        return self.build(investigation)
