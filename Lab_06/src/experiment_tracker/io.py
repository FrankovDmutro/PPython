"""File input and output utilities for CSV import and JSON export."""

import csv
import json
from pathlib import Path
from typing import Any

from experiment_tracker.exceptions import ExportError, ValidationError
from experiment_tracker.models import Experiment, Measurement, Researcher
from experiment_tracker.validators import (
    validate_iso_date,
    validate_measurement_value,
    validate_parameter,
    validate_unit,
)


def import_measurements_csv(path: Path) -> list[tuple[str, str, Researcher, str, Measurement]]:
    """Import scientific measurements from CSV file.

    Returns list of tuples: (experiment_id, title, researcher, parameter, measurement).
    Raises ValidationError on invalid schema or corrupted data.
    """
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    results: list[tuple[str, str, Researcher, str, Measurement]] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValidationError("CSV file is empty or missing headers", field="header")

        for line_num, row in enumerate(reader, start=2):
            exp_id = str(row.get("experiment_id", "")).strip()
            title = str(row.get("title", "")).strip()
            res_name = str(row.get("researcher", "")).strip()
            res_dept = str(row.get("department", "General Physics")).strip()
            param_raw = str(row.get("parameter", "")).strip()
            unit_raw = str(row.get("unit", "")).strip()
            val_raw = row.get("value")
            date_raw = str(row.get("date", "")).strip()

            if not exp_id:
                raise ValidationError("Missing experiment_id", field="experiment_id")
            if not res_name:
                raise ValidationError("Missing researcher name", field="researcher")

            param = validate_parameter(param_raw)
            unit = validate_unit(unit_raw)
            value = validate_measurement_value(val_raw, param)
            date_str = validate_iso_date(date_raw)

            researcher = Researcher(id=f"RES-{res_name.replace(' ', '_')}", name=res_name, department=res_dept)
            measurement = Measurement(value=value, unit=unit, timestamp=date_str)
            results.append((exp_id, title, researcher, param, measurement))

    return results


def export_experiment_json(experiment: Experiment, path: Path) -> Path:
    """Atomically export experiment to JSON file using temporary file replacement."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")

        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(experiment.to_dict(), f, ensure_ascii=False, indent=2)
            f.write("\n")

        temp_path.replace(path)
        return path
    except Exception as err:
        if "temp_path" in locals() and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise ExportError(f"Failed to export experiment '{experiment.id}' to {path}: {err}") from err
