import csv
from collections.abc import Iterable, Iterator
from log_processor.models import LogRecord


def parse_csv_rows(lines: Iterable[str]) -> Iterator[LogRecord]:
    """Генератор парсингу та базової валідації записів логів."""
    reader = csv.DictReader(lines)
    for row in reader:
        try:
            timestamp = row["timestamp"].strip()
            level = row["level"].strip()
            module = row["module"].strip()
            request_id = row["request_id"].strip()
            message = row["message"].strip()

            if not (timestamp and level and module and request_id and message):
                continue

            yield LogRecord(
                timestamp=timestamp,
                level=level,
                module=module,
                request_id=request_id,
                message=message,
            )
        except (KeyError, TypeError, ValueError):
            continue