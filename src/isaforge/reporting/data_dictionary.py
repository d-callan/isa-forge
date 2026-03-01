"""Data dictionary generation for custom terms."""

import json
from pathlib import Path

from isaforge.core.constants import DATA_DICTIONARY_FILE
from isaforge.observability.logger import get_logger
from isaforge.ontology.custom_terms import DataDictionary

logger = get_logger(__name__)


def generate_data_dictionary(
    dictionary: DataDictionary,
    output_dir: str | Path,
) -> Path:
    """Generate data_dictionary.json file.

    Args:
        dictionary: The DataDictionary model.
        output_dir: Directory to write the file to.

    Returns:
        Path to the generated file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / DATA_DICTIONARY_FILE

    # Convert to dictionary format
    output = dictionary.to_dict()

    # Write file
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        "data_dictionary_generated",
        path=str(output_path),
        term_count=len(dictionary.terms),
    )

    return output_path


def load_data_dictionary(file_path: str | Path) -> dict:
    """Load data dictionary from file.

    Args:
        file_path: Path to the data_dictionary.json file.

    Returns:
        Parsed data dictionary.
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    return json.loads(content)
