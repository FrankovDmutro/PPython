from collections.abc import Iterable, Iterator
from log_processor.models import LogRecord


def filter_by_level(records: Iterable[LogRecord], target_level: str) -> Iterator[LogRecord]:
    """Фільтрація логів за рівнем (наприклад, ERROR)."""
    for record in records:
        if record.level == target_level:
            yield record


def filter_by_module(records: Iterable[LogRecord], target_module: str) -> Iterator[LogRecord]:
    """Фільтрація логів за назвою модуля."""
    for record in records:
        if record.module == target_module:
            yield record


def find_by_request_id(records: Iterable[LogRecord], target_id: str) -> LogRecord | None:
    """Потоковий пошук запису за request_id з early termination."""
    for record in records:
        if record.request_id == target_id:
            return record
    return None