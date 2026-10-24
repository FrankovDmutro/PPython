"""Streaming data readers for CSV and other formats."""

import csv
from collections.abc import Iterator
from pathlib import Path

from experiment_importer.exceptions import DataImportError


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Stream CSV rows lazily one by one, yielding (line_number, row_dict).

    Memory footprint remains O(1) regardless of CSV file size.
    """
    if not path.is_file():
        raise DataImportError(f"Input file not found: {path}")

    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DataImportError(f"Input CSV file has no header: {path}")

            for line_number, row in enumerate(reader, start=2):
                yield line_number, row
    except OSError as error:
        raise DataImportError(f"Cannot read input file '{path}': {error}") from error
