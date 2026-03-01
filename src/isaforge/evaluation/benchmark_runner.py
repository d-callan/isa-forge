"""Benchmark runner for evaluating ISA-Forge against golden datasets."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from isaforge.evaluation.evaluator import EvaluationResult, ISATabEvaluator
from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""

    name: str
    golden_datasets_dir: Path
    output_dir: Path
    llm_provider: str = "anthropic"
    llm_model: str = "claude-3-sonnet"


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""

    config: BenchmarkConfig
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    dataset_results: list[EvaluationResult] = field(default_factory=list)

    # Aggregate metrics
    avg_accuracy: float = 0.0
    avg_precision: float = 0.0
    avg_recall: float = 0.0
    avg_f1_score: float = 0.0

    total_fields: int = 0
    total_exact_matches: int = 0
    total_mismatches: int = 0

    def calculate_aggregates(self) -> None:
        """Calculate aggregate metrics across all datasets."""
        if not self.dataset_results:
            return

        n = len(self.dataset_results)
        self.avg_accuracy = sum(r.accuracy for r in self.dataset_results) / n
        self.avg_precision = sum(r.precision for r in self.dataset_results) / n
        self.avg_recall = sum(r.recall for r in self.dataset_results) / n
        self.avg_f1_score = sum(r.f1_score for r in self.dataset_results) / n

        self.total_fields = sum(r.total_fields for r in self.dataset_results)
        self.total_exact_matches = sum(r.exact_matches for r in self.dataset_results)
        self.total_mismatches = sum(r.mismatches for r in self.dataset_results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": {
                "name": self.config.name,
                "golden_datasets_dir": str(self.config.golden_datasets_dir),
                "output_dir": str(self.config.output_dir),
                "llm_provider": self.config.llm_provider,
                "llm_model": self.config.llm_model,
            },
            "timing": {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            },
            "aggregate_metrics": {
                "avg_accuracy": round(self.avg_accuracy, 4),
                "avg_precision": round(self.avg_precision, 4),
                "avg_recall": round(self.avg_recall, 4),
                "avg_f1_score": round(self.avg_f1_score, 4),
                "total_fields": self.total_fields,
                "total_exact_matches": self.total_exact_matches,
                "total_mismatches": self.total_mismatches,
            },
            "dataset_count": len(self.dataset_results),
            "dataset_results": [r.to_dict() for r in self.dataset_results],
        }


class BenchmarkRunner:
    """Runner for benchmark evaluations."""

    def __init__(self, config: BenchmarkConfig):
        """Initialize the runner.

        Args:
            config: Benchmark configuration.
        """
        self.config = config
        self.evaluator = ISATabEvaluator()

    def discover_golden_datasets(self) -> list[Path]:
        """Discover golden datasets in the configured directory.

        Returns:
            List of paths to golden dataset directories.
        """
        datasets = []
        golden_dir = self.config.golden_datasets_dir

        if not golden_dir.exists():
            logger.warning("golden_datasets_dir_not_found", path=str(golden_dir))
            return datasets

        # Each subdirectory with i_investigation.txt is a dataset
        for subdir in golden_dir.iterdir():
            if subdir.is_dir():
                investigation = subdir / "i_investigation.txt"
                if investigation.exists():
                    datasets.append(subdir)

        logger.info("golden_datasets_discovered", count=len(datasets))
        return datasets

    def run(self, generated_dirs: dict[str, Path]) -> BenchmarkResult:
        """Run benchmark evaluation.

        Args:
            generated_dirs: Mapping of dataset_id -> generated output directory.

        Returns:
            Benchmark result with all evaluations.
        """
        result = BenchmarkResult(config=self.config)

        golden_datasets = self.discover_golden_datasets()

        for golden_dir in golden_datasets:
            dataset_id = golden_dir.name

            if dataset_id not in generated_dirs:
                logger.warning("no_generated_output", dataset_id=dataset_id)
                continue

            generated_dir = generated_dirs[dataset_id]

            try:
                eval_result = self.evaluator.evaluate(
                    generated_dir=generated_dir,
                    golden_dir=golden_dir,
                    session_id=f"benchmark_{dataset_id}",
                    golden_dataset_id=dataset_id,
                )
                result.dataset_results.append(eval_result)

                logger.info(
                    "dataset_evaluated",
                    dataset_id=dataset_id,
                    accuracy=eval_result.accuracy,
                )

            except Exception as e:
                logger.error(
                    "dataset_evaluation_failed",
                    dataset_id=dataset_id,
                    error=str(e),
                )

        result.completed_at = datetime.utcnow()
        result.calculate_aggregates()

        logger.info(
            "benchmark_completed",
            datasets_evaluated=len(result.dataset_results),
            avg_f1_score=result.avg_f1_score,
        )

        return result

    def save_results(self, result: BenchmarkResult) -> Path:
        """Save benchmark results to file.

        Args:
            result: Benchmark result to save.

        Returns:
            Path to saved results file.
        """
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_{self.config.name}_{timestamp}.json"
        output_path = output_dir / filename

        output_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        logger.info("benchmark_results_saved", path=str(output_path))
        return output_path


def load_benchmark_result(path: str | Path) -> dict[str, Any]:
    """Load benchmark results from file.

    Args:
        path: Path to benchmark results JSON file.

    Returns:
        Parsed benchmark results.
    """
    path = Path(path)
    content = path.read_text(encoding="utf-8")
    return json.loads(content)
