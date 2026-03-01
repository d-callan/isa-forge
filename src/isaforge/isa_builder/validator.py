"""ISA-Tab validation using isatools."""

from pathlib import Path
from typing import Any

from isaforge.core.config import settings
from isaforge.core.exceptions import ISAValidationError
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class ISATabValidator:
    """Validator for ISA-Tab files using isatools."""

    def __init__(self, strict: bool | None = None):
        """Initialize the validator.

        Args:
            strict: Whether to use strict validation. Defaults to settings.
        """
        self.strict = strict if strict is not None else settings.validation_strict

    def validate(self, isa_dir: str | Path) -> dict[str, Any]:
        """Validate ISA-Tab files in a directory.

        Args:
            isa_dir: Path to directory containing ISA-Tab files.

        Returns:
            Validation results dictionary.

        Raises:
            ISAValidationError: If validation fails in strict mode.
        """
        isa_dir = Path(isa_dir)

        if not isa_dir.exists():
            raise ISAValidationError(f"Directory not found: {isa_dir}")

        # Check for investigation file
        investigation_file = isa_dir / "i_investigation.txt"
        if not investigation_file.exists():
            raise ISAValidationError(f"Investigation file not found: {investigation_file}")

        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
        }

        try:
            # Try to use isatools for validation
            from isatools import isatab

            # Load and validate
            with open(investigation_file, encoding="utf-8") as f:
                investigation = isatab.load(f)

            # If we got here, basic parsing succeeded
            results["info"].append("ISA-Tab files parsed successfully")

            # Check for studies
            if hasattr(investigation, "studies"):
                results["info"].append(f"Found {len(investigation.studies)} study/studies")

            logger.info(
                "isa_validation_success",
                isa_dir=str(isa_dir),
            )

        except ImportError:
            # isatools not available, do basic validation
            results["warnings"].append(
                "isatools not available, performing basic validation only"
            )
            results = self._basic_validation(isa_dir, results)

        except Exception as e:
            error_msg = f"Validation error: {e}"
            results["errors"].append(error_msg)
            results["valid"] = False

            logger.error(
                "isa_validation_error",
                isa_dir=str(isa_dir),
                error=str(e),
            )

            if self.strict:
                raise ISAValidationError(error_msg) from e

        return results

    def _basic_validation(
        self,
        isa_dir: Path,
        results: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform basic validation without isatools.

        Args:
            isa_dir: Path to ISA-Tab directory.
            results: Results dictionary to update.

        Returns:
            Updated results dictionary.
        """
        # Check investigation file
        investigation_file = isa_dir / "i_investigation.txt"
        try:
            content = investigation_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")

            # Check for required sections
            required_sections = [
                "ONTOLOGY SOURCE REFERENCE",
                "INVESTIGATION",
                "STUDY",
            ]

            found_sections = set()
            for line in lines:
                for section in required_sections:
                    if line.strip() == section:
                        found_sections.add(section)

            missing_sections = set(required_sections) - found_sections
            if missing_sections:
                results["warnings"].append(
                    f"Missing sections: {', '.join(missing_sections)}"
                )

            results["info"].append(f"Investigation file has {len(lines)} lines")

        except Exception as e:
            results["errors"].append(f"Error reading investigation file: {e}")
            results["valid"] = False

        # Check for study files
        study_files = list(isa_dir.glob("s_*.txt"))
        if not study_files:
            results["warnings"].append("No study files found")
        else:
            results["info"].append(f"Found {len(study_files)} study file(s)")

        # Check for assay files
        assay_files = list(isa_dir.glob("a_*.txt"))
        if not assay_files:
            results["warnings"].append("No assay files found")
        else:
            results["info"].append(f"Found {len(assay_files)} assay file(s)")

        return results

    def validate_investigation(self, investigation_path: str | Path) -> dict[str, Any]:
        """Validate a single investigation file.

        Args:
            investigation_path: Path to investigation file.

        Returns:
            Validation results dictionary.
        """
        investigation_path = Path(investigation_path)

        if not investigation_path.exists():
            raise ISAValidationError(f"File not found: {investigation_path}")

        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
        }

        try:
            content = investigation_path.read_text(encoding="utf-8")
            lines = content.strip().split("\n")

            # Check basic structure
            if not lines:
                results["errors"].append("Empty investigation file")
                results["valid"] = False
                return results

            # Check for tab-delimited format
            has_tabs = any("\t" in line for line in lines)
            if not has_tabs:
                results["warnings"].append(
                    "No tab characters found - file may not be properly formatted"
                )

            results["info"].append(f"File has {len(lines)} lines")

        except Exception as e:
            results["errors"].append(f"Error reading file: {e}")
            results["valid"] = False

        return results
