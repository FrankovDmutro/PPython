from collections.abc import Iterator
from pathlib import Path
from log_processor.filters import filter_by_level, filter_by_module
from log_processor.models import LogRecord
from log_processor.parsers import parse_csv_rows
from log_processor.readers import read_lines
from log_processor.transformations import normalize_log_messages


def build_log_pipeline(
    path: Path,
    level: str | None = None,
    module: str | None = None,
) -> Iterator[LogRecord]:
    """Створює lazy-пайплайн обробки логів."""
    lines = read_lines(path)
    records = parse_csv_rows(lines)
    transformed = normalize_log_messages(records)

    filtered = transformed
    if level is not None:
        filtered = filter_by_level(filtered, level)
    if module is not None:
        filtered = filter_by_module(filtered, module)

    return filtered