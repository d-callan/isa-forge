"""Evaluation framework for ISA-Tab generation quality."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from isaforge.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FieldComparison:
    """Comparison result for a single field."""

    field_path: str
    expected: Any
    actual: Any
    match: bool
    similarity: float = 1.0  # 1.0 for exact match, 0.0-1.0 for partial
    notes: str = ""


@dataclass
class EvaluationResult:
    """Result of evaluating generated ISA-Tab against golden dataset."""

    session_id: str
    golden_dataset_id: str

    # Field-level metrics
    field_comparisons: list[FieldComparison] = field(default_factory=list)
    total_fields: int = 0
    exact_matches: int = 0
    partial_matches: int = 0
    mismatches: int = 0
    missing_fields: int = 0
    extra_fields: int = 0

    # Aggregate metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Confidence calibration
    avg_confidence_correct: float = 0.0
    avg_confidence_incorrect: float = 0.0
    calibration_error: float = 0.0

    # Ontology metrics
    ontology_accuracy: float = 0.0
    custom_term_rate: float = 0.0

    def calculate_metrics(self) -> None:
        """Calculate aggregate metrics from field comparisons."""
        if not self.field_comparisons:
            return

        self.total_fields = len(self.field_comparisons)
        self.exact_matches = sum(1 for fc in self.field_comparisons if fc.match and fc.similarity == 1.0)
        self.partial_matches = sum(1 for fc in self.field_comparisons if fc.match and fc.similarity < 1.0)
        self.mismatches = sum(1 for fc in self.field_comparisons if not fc.match)

        # Accuracy: exact matches / total
        self.accuracy = self.exact_matches / self.total_fields if self.total_fields > 0 else 0.0

        # Precision: correct / (correct + extra)
        correct = self.exact_matches + self.partial_matches
        if correct + self.extra_fields > 0:
            self.precision = correct / (correct + self.extra_fields)

        # Recall: correct / (correct + missing)
        if correct + self.missing_fields > 0:
            self.recall = correct / (correct + self.missing_fields)

        # F1 score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "golden_dataset_id": self.golden_dataset_id,
            "metrics": {
                "total_fields": self.total_fields,
                "exact_matches": self.exact_matches,
                "partial_matches": self.partial_matches,
                "mismatches": self.mismatches,
                "missing_fields": self.missing_fields,
                "extra_fields": self.extra_fields,
                "accuracy": round(self.accuracy, 4),
                "precision": round(self.precision, 4),
                "recall": round(self.recall, 4),
                "f1_score": round(self.f1_score, 4),
            },
            "confidence_calibration": {
                "avg_confidence_correct": round(self.avg_confidence_correct, 4),
                "avg_confidence_incorrect": round(self.avg_confidence_incorrect, 4),
                "calibration_error": round(self.calibration_error, 4),
            },
            "ontology_metrics": {
                "ontology_accuracy": round(self.ontology_accuracy, 4),
                "custom_term_rate": round(self.custom_term_rate, 4),
            },
            "field_comparisons": [
                {
                    "field_path": fc.field_path,
                    "expected": fc.expected,
                    "actual": fc.actual,
                    "match": fc.match,
                    "similarity": round(fc.similarity, 4),
                    "notes": fc.notes,
                }
                for fc in self.field_comparisons
            ],
        }


class ISATabEvaluator:
    """Evaluator for comparing generated ISA-Tab against golden datasets."""

    def __init__(self):
        """Initialize the evaluator."""
        pass

    def evaluate(
        self,
        generated_dir: str | Path,
        golden_dir: str | Path,
        session_id: str,
        golden_dataset_id: str,
    ) -> EvaluationResult:
        """Evaluate generated ISA-Tab against golden dataset.

        Args:
            generated_dir: Directory with generated ISA-Tab files.
            golden_dir: Directory with golden ISA-Tab files.
            session_id: Session ID of the generation.
            golden_dataset_id: ID of the golden dataset.

        Returns:
            Evaluation result with metrics.
        """
        generated_dir = Path(generated_dir)
        golden_dir = Path(golden_dir)

        result = EvaluationResult(
            session_id=session_id,
            golden_dataset_id=golden_dataset_id,
        )

        # Compare investigation files
        gen_investigation = generated_dir / "i_investigation.txt"
        gold_investigation = golden_dir / "i_investigation.txt"

        if gen_investigation.exists() and gold_investigation.exists():
            comparisons = self._compare_investigation_files(
                gen_investigation, gold_investigation
            )
            result.field_comparisons.extend(comparisons)

        # Compare study files
        for gen_study in generated_dir.glob("s_*.txt"):
            gold_study = golden_dir / gen_study.name
            if gold_study.exists():
                comparisons = self._compare_tabular_files(gen_study, gold_study)
                result.field_comparisons.extend(comparisons)

        # Compare assay files
        for gen_assay in generated_dir.glob("a_*.txt"):
            gold_assay = golden_dir / gen_assay.name
            if gold_assay.exists():
                comparisons = self._compare_tabular_files(gen_assay, gold_assay)
                result.field_comparisons.extend(comparisons)

        # Calculate metrics
        result.calculate_metrics()

        logger.info(
            "evaluation_completed",
            session_id=session_id,
            accuracy=result.accuracy,
            f1_score=result.f1_score,
        )

        return result

    def _compare_investigation_files(
        self,
        generated: Path,
        golden: Path,
    ) -> list[FieldComparison]:
        """Compare investigation files field by field.

        Args:
            generated: Path to generated investigation file.
            golden: Path to golden investigation file.

        Returns:
            List of field comparisons.
        """
        comparisons = []

        gen_fields = self._parse_investigation_file(generated)
        gold_fields = self._parse_investigation_file(golden)

        # Compare all golden fields
        for field_path, expected in gold_fields.items():
            actual = gen_fields.get(field_path)

            if actual is None:
                comparisons.append(FieldComparison(
                    field_path=field_path,
                    expected=expected,
                    actual=None,
                    match=False,
                    similarity=0.0,
                    notes="Field missing in generated",
                ))
            elif actual == expected:
                comparisons.append(FieldComparison(
                    field_path=field_path,
                    expected=expected,
                    actual=actual,
                    match=True,
                    similarity=1.0,
                ))
            else:
                similarity = self._calculate_similarity(expected, actual)
                comparisons.append(FieldComparison(
                    field_path=field_path,
                    expected=expected,
                    actual=actual,
                    match=similarity >= 0.8,
                    similarity=similarity,
                ))

        return comparisons

    def _compare_tabular_files(
        self,
        generated: Path,
        golden: Path,
    ) -> list[FieldComparison]:
        """Compare tabular (study/assay) files.

        Args:
            generated: Path to generated file.
            golden: Path to golden file.

        Returns:
            List of field comparisons.
        """
        comparisons = []

        gen_rows = self._parse_tabular_file(generated)
        gold_rows = self._parse_tabular_file(golden)

        # Compare row counts
        if len(gen_rows) != len(gold_rows):
            comparisons.append(FieldComparison(
                field_path=f"{generated.name}:row_count",
                expected=len(gold_rows),
                actual=len(gen_rows),
                match=False,
                similarity=min(len(gen_rows), len(gold_rows)) / max(len(gen_rows), len(gold_rows)) if max(len(gen_rows), len(gold_rows)) > 0 else 0,
            ))

        # Compare individual rows
        for i, (gen_row, gold_row) in enumerate(zip(gen_rows, gold_rows)):
            for col, expected in gold_row.items():
                actual = gen_row.get(col)
                field_path = f"{generated.name}:row{i}:{col}"

                if actual == expected:
                    comparisons.append(FieldComparison(
                        field_path=field_path,
                        expected=expected,
                        actual=actual,
                        match=True,
                        similarity=1.0,
                    ))
                else:
                    similarity = self._calculate_similarity(expected, actual)
                    comparisons.append(FieldComparison(
                        field_path=field_path,
                        expected=expected,
                        actual=actual,
                        match=similarity >= 0.8,
                        similarity=similarity,
                    ))

        return comparisons

    def _parse_investigation_file(self, path: Path) -> dict[str, str]:
        """Parse investigation file into field dictionary.

        Args:
            path: Path to investigation file.

        Returns:
            Dictionary of field_name -> value.
        """
        fields = {}
        content = path.read_text(encoding="utf-8")

        current_section = ""
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            if not line.startswith("\t") and "\t" not in line:
                # Section header
                current_section = line
            elif "\t" in line:
                parts = line.split("\t")
                field_name = parts[0]
                values = parts[1:] if len(parts) > 1 else [""]
                field_path = f"{current_section}.{field_name}"
                fields[field_path] = "\t".join(values)

        return fields

    def _parse_tabular_file(self, path: Path) -> list[dict[str, str]]:
        """Parse tabular file into list of row dictionaries.

        Args:
            path: Path to tabular file.

        Returns:
            List of row dictionaries.
        """
        rows = []
        content = path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        if not lines:
            return rows

        headers = lines[0].split("\t")

        for line in lines[1:]:
            values = line.split("\t")
            row = {}
            for i, header in enumerate(headers):
                row[header] = values[i] if i < len(values) else ""
            rows.append(row)

        return rows

    def _calculate_similarity(self, expected: Any, actual: Any) -> float:
        """Calculate similarity between expected and actual values.

        Args:
            expected: Expected value.
            actual: Actual value.

        Returns:
            Similarity score 0.0-1.0.
        """
        if expected == actual:
            return 1.0

        if expected is None or actual is None:
            return 0.0

        # String similarity using simple character overlap
        expected_str = str(expected).lower()
        actual_str = str(actual).lower()

        if not expected_str or not actual_str:
            return 0.0

        # Jaccard similarity on character n-grams
        def get_ngrams(s: str, n: int = 2) -> set:
            return set(s[i:i+n] for i in range(len(s) - n + 1))

        expected_ngrams = get_ngrams(expected_str)
        actual_ngrams = get_ngrams(actual_str)

        if not expected_ngrams or not actual_ngrams:
            return 1.0 if expected_str == actual_str else 0.0

        intersection = len(expected_ngrams & actual_ngrams)
        union = len(expected_ngrams | actual_ngrams)

        return intersection / union if union > 0 else 0.0
