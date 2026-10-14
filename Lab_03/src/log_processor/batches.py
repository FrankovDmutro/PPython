from collections.abc import Iterable, Iterator
from itertools import islice
from log_processor.models import LogRecord


def batched_logs(records: Iterable[LogRecord], batch_size: int) -> Iterator[list[LogRecord]]:
    """Розбиття потоку логів на пакети заданого розміру."""
    iterator = iter(records)
    while True:
        batch = list(islice(iterator, batch_size))
        if not batch:
            return
        yield batch