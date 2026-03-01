"""Confidence summary report generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from isaforge.core.constants import CONFIDENCE_SUMMARY_FILE
from isaforge.models.confidence import ConfidenceSummary
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


def generate_confidence_summary(
    summary: ConfidenceSummary,
    output_dir: str | Path,
) -> Path:
    """Generate confidence_summary.json file.

    Args:
        summary: The ConfidenceSummary model.
        output_dir: Directory to write the file to.

    Returns:
        Path to the generated file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / CONFIDENCE_SUMMARY_FILE

    # Update stats before export
    summary.update_stats()

    # Build output structure
    output = {
        "session_id": summary.session_id,
        "created_at": summary.created_at.isoformat(),
        "summary": {
            "total_fields": summary.total_fields,
            "auto_accepted": summary.auto_accepted,
            "user_confirmed": summary.user_confirmed,
            "user_edited": summary.user_edited,
            "flagged": summary.flagged,
            "pending": summary.pending,
            "average_confidence": round(summary.average_confidence, 3),
            "min_confidence": round(summary.min_confidence, 3),
            "max_confidence": round(summary.max_confidence, 3),
        },
        "fields": {},
    }

    # Add field details
    for field_path, field_conf in summary.fields.items():
        output["fields"][field_path] = {
            "value": field_conf.value,
            "confidence": round(field_conf.confidence, 3),
            "justification": field_conf.justification,
            "source": field_conf.source.value,
            "user_action": field_conf.user_action.value,
            "alternatives": field_conf.alternatives,
            "created_at": field_conf.created_at.isoformat(),
            "updated_at": field_conf.updated_at.isoformat(),
        }

    # Write file
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        "confidence_summary_generated",
        path=str(output_path),
        total_fields=summary.total_fields,
    )

    return output_path


def load_confidence_summary(file_path: str | Path) -> dict[str, Any]:
    """Load a confidence summary from file.

    Args:
        file_path: Path to the confidence_summary.json file.

    Returns:
        Parsed confidence summary dictionary.
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    return json.loads(content)
