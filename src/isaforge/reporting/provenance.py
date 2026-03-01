"""Provenance tracking and report generation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from isaforge.core.constants import PROVENANCE_FILE
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


class DataSourceProvenance(BaseModel):
    """Provenance information for a data source."""

    source_type: str = Field(..., description="Type of source (bioproject, publication, local_file)")
    identifier: str = Field(..., description="Source identifier")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    url: str | None = Field(default=None, description="URL if applicable")


class FieldProvenance(BaseModel):
    """Provenance information for a field."""

    source: str = Field(..., description="Source of the value")
    llm_confidence: float | None = Field(default=None, description="LLM confidence score")
    user_action: str = Field(default="pending", description="User action taken")
    llm_call_id: str | None = Field(default=None, description="ID of LLM call that generated this")


class CorrectionInfo(BaseModel):
    """Information about a user correction."""

    field_path: str = Field(..., description="Path to the corrected field")
    original_value: str | None = Field(default=None, description="Original value")
    corrected_value: str | None = Field(default=None, description="Corrected value")
    correction_type: str = Field(..., description="Type of correction")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConfidenceSnapshot(BaseModel):
    """A snapshot of confidence at a point in time."""

    confidence: float = Field(..., description="Confidence score")
    justification: str | None = Field(default=None, description="Justification")
    source: str | None = Field(default=None, description="Source")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ProvenanceRecord(BaseModel):
    """Complete provenance record for a session."""

    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    llm_provider: str = Field(..., description="LLM provider used")
    llm_model: str = Field(..., description="LLM model used")

    data_sources: list[DataSourceProvenance] = Field(
        default_factory=list, description="Data sources used"
    )
    field_provenance: dict[str, FieldProvenance] = Field(
        default_factory=dict, description="Per-field provenance"
    )

    total_llm_calls: int = Field(default=0, description="Total LLM calls made")
    total_tokens: int = Field(default=0, description="Total tokens used")
    generation_time_seconds: float | None = Field(
        default=None, description="Total generation time"
    )

    # Enhanced tracking fields
    prompt_hashes_used: list[str] = Field(
        default_factory=list, description="Unique prompt hashes used in this session"
    )
    corrections: list[CorrectionInfo] = Field(
        default_factory=list, description="User corrections made"
    )
    confidence_history: dict[str, list[ConfidenceSnapshot]] = Field(
        default_factory=dict, description="Confidence history per field"
    )


def generate_provenance(
    record: ProvenanceRecord,
    output_dir: str | Path,
) -> Path:
    """Generate provenance.json file.

    Args:
        record: The ProvenanceRecord model.
        output_dir: Directory to write the file to.

    Returns:
        Path to the generated file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / PROVENANCE_FILE

    # Build output structure
    output = {
        "session_id": record.session_id,
        "created_at": record.created_at.isoformat(),
        "llm": {
            "provider": record.llm_provider,
            "model": record.llm_model,
            "total_calls": record.total_llm_calls,
            "total_tokens": record.total_tokens,
        },
        "data_sources": [
            {
                "type": ds.source_type,
                "identifier": ds.identifier,
                "retrieved_at": ds.retrieved_at.isoformat(),
                "url": ds.url,
            }
            for ds in record.data_sources
        ],
        "field_provenance": {
            field_path: {
                "source": fp.source,
                "llm_confidence": fp.llm_confidence,
                "user_action": fp.user_action,
                "llm_call_id": fp.llm_call_id,
            }
            for field_path, fp in record.field_provenance.items()
        },
        "generation_time_seconds": record.generation_time_seconds,
        "prompt_hashes_used": record.prompt_hashes_used,
        "corrections": [
            {
                "field_path": c.field_path,
                "original_value": c.original_value,
                "corrected_value": c.corrected_value,
                "correction_type": c.correction_type,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in record.corrections
        ],
        "confidence_history": {
            field_path: [
                {
                    "confidence": snap.confidence,
                    "justification": snap.justification,
                    "source": snap.source,
                    "timestamp": snap.timestamp.isoformat(),
                }
                for snap in snapshots
            ]
            for field_path, snapshots in record.confidence_history.items()
        },
        "summary": {
            "total_corrections": len(record.corrections),
            "unique_prompts": len(record.prompt_hashes_used),
            "fields_with_history": len(record.confidence_history),
        },
    }

    # Write file
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        "provenance_generated",
        path=str(output_path),
        data_source_count=len(record.data_sources),
    )

    return output_path


def load_provenance(file_path: str | Path) -> dict[str, Any]:
    """Load provenance from file.

    Args:
        file_path: Path to the provenance.json file.

    Returns:
        Parsed provenance dictionary.
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    return json.loads(content)
