from collections import Counter
from collections.abc import Iterable, Iterator
from itertools import groupby
from log_processor.models import LogRecord


def calculate_log_summary(records: Iterable[LogRecord]) -> dict:
    """Потокова агрегація статистики без повної матеріалізації списку в пам'яті."""
    total_count = 0
    level_counts = Counter()
    module_counts = Counter()

    for record in records:
        total_count += 1
        level_counts[record.level] += 1
        module_counts[record.module] += 1

    return {
        "total_records": total_count,
        "level_counts": dict(level_counts),
        "module_counts": dict(module_counts),
    }


def group_consecutive_levels(records: Iterable[LogRecord]) -> Iterator[tuple[str, int]]:
    """Групування послідовних однакових рівнів логів через itertools.groupby."""
    for level, group in groupby(records, key=lambda item: item.level):
        count = sum(1 for _ in group)
        yield level, count