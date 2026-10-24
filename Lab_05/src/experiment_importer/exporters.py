"""Exporters supporting atomic streaming JSON and JSON Lines."""

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Any

from experiment_importer.context_managers import atomic_write
from experiment_importer.exceptions import DataExportError
from experiment_importer.models import ExperimentRecord


def export_experiments_json(
    records: Iterable[ExperimentRecord],
    path: Path,
) -> int:
    """Atomically export experiment records as a formatted streaming JSON array.

    Ensures that file output is atomic: writes to temporary file and renames upon success.
    Returns the total count of exported records.
    """
    count = 0
    try:
        with atomic_write(path) as file:
            file.write("[\n")
            first = True
            for record in records:
                if not first:
                    file.write(",\n")
                # Indented JSON block for readability
                item_json = json.dumps(record.to_dict(), ensure_ascii=False, indent=2)
                # Indent lines
                indented = "\n".join("  " + line for line in item_json.splitlines())
                file.write(indented)
                first = False
                count += 1
            file.write("\n]\n")
    except Exception as error:
        raise DataExportError(f"Cannot export experiments to JSON file '{path}': {error}") from error

    return count


def export_experiments_jsonl(
    records: Iterable[ExperimentRecord],
    path: Path,
) -> int:
    """Atomically export experiment records in streaming JSON Lines format.

    Each line represents a complete JSON object.
    Ideal for massive streaming pipelines.
    """
    count = 0
    try:
        with atomic_write(path) as file:
            for record in records:
                line = json.dumps(record.to_dict(), ensure_ascii=False)
                file.write(line + "\n")
                count += 1
    except Exception as error:
        raise DataExportError(f"Cannot export experiments to JSON Lines file '{path}': {error}") from error

    return count


def export_summary_json(summary: dict[str, Any], path: Path) -> None:
    """Atomically export process summary and statistics as formatted JSON."""
    try:
        with atomic_write(path) as file:
            json.dump(summary, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except Exception as error:
        raise DataExportError(f"Cannot export summary to JSON file '{path}': {error}") from error
