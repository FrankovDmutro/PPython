from collections.abc import Iterable, Iterator
from log_processor.models import LogRecord


def normalize_log_messages(records: Iterable[LogRecord]) -> Iterator[LogRecord]:
    """Генератор нормалізації тексту повідомлення."""
    for record in records:
        yield record._replace(message=record.message.strip().capitalize())  