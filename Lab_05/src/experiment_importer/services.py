"""Core service layer for experiment processing, statistics, and filtering."""

from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any

from experiment_importer.context_managers import logged_operation
from experiment_importer.exceptions import RecordValidationError
from experiment_importer.exporters import (
    export_experiments_json,
    export_experiments_jsonl,
    export_summary_json,
)
from experiment_importer.models import AppConfig, ExperimentRecord, ProcessingConfig
from experiment_importer.readers import read_csv_rows
from experiment_importer.validators import parse_experiment

logger = logging.getLogger(__name__)


@dataclass
class ImportStatistics:
    """Aggregator for import process statistics, metrics, and error logs."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    parameter_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    parameter_sums: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    parameter_mins: dict[str, float] = field(default_factory=dict)
    parameter_maxs: dict[str, float] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def record_valid(self, record: ExperimentRecord) -> None:
        """Update metrics for a successfully validated record."""
        self.valid += 1
        param = record.parameter
        self.parameter_counts[param] += 1
        self.parameter_sums[param] += record.result

        if param not in self.parameter_mins or record.result < self.parameter_mins[param]:
            self.parameter_mins[param] = record.result
        if param not in self.parameter_maxs or record.result > self.parameter_maxs[param]:
            self.parameter_maxs[param] = record.result

    def record_invalid(self, error: RecordValidationError) -> None:
        """Register a validation failure."""
        self.invalid += 1
        self.errors.append({
            "line": error.line_number,
            "field": error.field,
            "message": error.message,
            "raw_value": str(error.raw_value),
        })

    def to_dict(self) -> dict[str, Any]:
        """Convert statistics to structured report dictionary."""
        per_parameter: dict[str, dict[str, float]] = {}
        for param, count in self.parameter_counts.items():
            avg = self.parameter_sums[param] / count if count > 0 else 0.0
            per_parameter[param] = {
                "count": count,
                "average": round(avg, 4),
                "min": round(self.parameter_mins.get(param, 0.0), 4),
                "max": round(self.parameter_maxs.get(param, 0.0), 4),
            }

        return {
            "total_records": self.total,
            "valid_records": self.valid,
            "invalid_records": self.invalid,
            "success_rate_percent": round((self.valid / self.total * 100), 2) if self.total else 0.0,
            "parameter_metrics": per_parameter,
            "error_samples": self.errors[:20],  # sample of first 20 errors
        }


def import_experiments(
    path: Path,
    config: ProcessingConfig,
    statistics: ImportStatistics,
) -> Iterator[ExperimentRecord]:
    """Stream and validate experiments from CSV file.

    In tolerant mode (skip_invalid=True), invalid rows are logged and skipped.
    In strict mode (skip_invalid=False), the first invalid row terminates processing.
    """
    for line_number, row in read_csv_rows(path):
        statistics.total += 1
        try:
            record = parse_experiment(row, line_number=line_number, config=config)
            statistics.record_valid(record)
            yield record
        except RecordValidationError as error:
            statistics.record_invalid(error)
            logger.warning("Validation failed at line %d: %s", line_number, error)
            if not config.skip_invalid:
                logger.error("Strict mode enabled: aborting import on line %d", line_number)
                raise


def filter_by_parameter(
    records: Iterable[ExperimentRecord],
    parameter: str,
) -> Iterator[ExperimentRecord]:
    """Filter experiment stream by physical parameter name."""
    target = parameter.strip().lower()
    for record in records:
        if record.parameter.lower() == target:
            yield record


def run_pipeline(
    config: AppConfig,
    *,
    output_format: str = "json",
    override_skip_invalid: bool | None = None,
) -> tuple[int, ImportStatistics]:
    """Execute complete ingestion and export pipeline according to configuration."""
    proc_config = config.processing
    if override_skip_invalid is not None:
        proc_config = ProcessingConfig(
            allowed_parameters=proc_config.allowed_parameters,
            min_result=proc_config.min_result,
            max_result=proc_config.max_result,
            skip_invalid=override_skip_invalid,
        )

    mode_label = "Tolerant" if proc_config.skip_invalid else "Strict"
    operation_name = f"Scientific Experiment Processing Pipeline ({mode_label} mode)"

    statistics = ImportStatistics()

    with logged_operation(operation_name):
        records_stream = import_experiments(
            config.input_path,
            proc_config,
            statistics,
        )

        if output_format.lower() == "jsonl":
            exported_count = export_experiments_jsonl(records_stream, config.output_path)
        else:
            exported_count = export_experiments_json(records_stream, config.output_path)

        # Export summary if configured
        export_summary_json(statistics.to_dict(), config.summary_path)

        logger.info(
            "Pipeline finished. Total: %d, Valid: %d, Invalid: %d, Exported: %d",
            statistics.total,
            statistics.valid,
            statistics.invalid,
            exported_count,
        )

    return exported_count, statistics
