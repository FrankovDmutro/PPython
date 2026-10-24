"""Validation logic for experiment records with detailed error tracking."""

from datetime import date
from typing import Any

from experiment_importer.exceptions import RecordValidationError
from experiment_importer.models import ExperimentRecord, ProcessingConfig


def parse_experiment(
    row: dict[str, Any],
    *,
    line_number: int,
    config: ProcessingConfig,
) -> ExperimentRecord:
    """Validate and parse raw dictionary row into ExperimentRecord domain model.

    Raises RecordValidationError with contextual information upon validation failure.
    """
    # 1. Validate experiment_id
    raw_id = str(row.get("experiment_id", "")).strip()
    if not raw_id:
        raise RecordValidationError(
            "experiment_id cannot be empty",
            line_number=line_number,
            field="experiment_id",
            raw_value=row.get("experiment_id"),
        )

    # 2. Validate experiment name
    name = str(row.get("name", "")).strip()
    if not name:
        raise RecordValidationError(
            "Experiment name cannot be empty",
            line_number=line_number,
            field="name",
            raw_value=row.get("name"),
        )

    # 3. Validate researcher
    researcher = str(row.get("researcher", "")).strip()
    if not researcher:
        raise RecordValidationError(
            "Researcher name cannot be empty",
            line_number=line_number,
            field="researcher",
            raw_value=row.get("researcher"),
        )

    # 4. Validate parameter against allowed list
    raw_param = str(row.get("parameter", "")).strip().lower()
    if not raw_param:
        raise RecordValidationError(
            "Parameter name cannot be empty",
            line_number=line_number,
            field="parameter",
            raw_value=row.get("parameter"),
        )
    if raw_param not in config.allowed_parameters:
        raise RecordValidationError(
            f"Parameter '{raw_param}' is not in allowed parameters list: {config.allowed_parameters}",
            line_number=line_number,
            field="parameter",
            raw_value=raw_param,
        )

    # 5. Validate result numeric value and range
    raw_result = row.get("result")
    try:
        result = float(raw_result)  # type: ignore[arg-type]
    except (ValueError, TypeError) as err:
        raise RecordValidationError(
            f"Measurement result must be a valid float, got '{raw_result}'",
            line_number=line_number,
            field="result",
            raw_value=raw_result,
        ) from err

    if not (config.min_result <= result <= config.max_result):
        raise RecordValidationError(
            f"Measurement result {result} is outside allowed range [{config.min_result}, {config.max_result}]",
            line_number=line_number,
            field="result",
            raw_value=result,
        )

    # 6. Validate date format (YYYY-MM-DD)
    raw_date = str(row.get("date", "")).strip()
    if not raw_date:
        raise RecordValidationError(
            "Experiment date cannot be empty",
            line_number=line_number,
            field="date",
            raw_value=row.get("date"),
        )
    try:
        parsed_date = date.fromisoformat(raw_date)
    except ValueError as err:
        raise RecordValidationError(
            f"Experiment date must be in ISO format (YYYY-MM-DD), got '{raw_date}'",
            line_number=line_number,
            field="date",
            raw_value=raw_date,
        ) from err

    return ExperimentRecord(
        experiment_id=raw_id,
        name=name,
        researcher=researcher,
        parameter=raw_param,
        result=result,
        date=parsed_date.isoformat(),
    )
