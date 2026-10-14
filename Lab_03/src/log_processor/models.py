from collections.abc import Iterator
from typing import NamedTuple


class LogRecord(NamedTuple):
    timestamp: str
    level: str
    module: str
    request_id: str
    message: str


class SimpleLogRangeIterator:
    """Власний клас-ітератор для демонстрації Iterator Protocol."""

    def __init__(self, records: list[LogRecord], stop: int) -> None:
        self.records = records
        self.stop = min(stop, len(records))
        self.current = 0

    def __iter__(self) -> Iterator[LogRecord]:
        return self

    def __next__(self) -> LogRecord:
        if self.current >= self.stop:
            raise StopIteration
        record = self.records[self.current]
        self.current += 1
        return record