from collections import Counter
from collections.abc import Callable
from .decorators import measure_time

@measure_time
def calculate_error_rate(logs: list[dict]) -> float:
    """
    Рахує частку помилок (ERROR + CRITICAL) за допомогою генераторного виразу.
    Декорована функція для вимірювання часу.
    """
    if not logs:
        return 0.0
    error_count = sum(1 for log in logs if log["level"] in {"ERROR", "CRITICAL"})
    return (error_count / len(logs)) * 100.0

def rank_modules_by_errors(logs: list[dict]) -> list[tuple[str, int]]:
    """
    Формує рейтинг модулів за кількістю помилок (ERROR) у порядку спадання.
    Використовує Counter та сортування за допомогою lambda.
    """
    error_logs = [log for log in logs if log["level"] == "ERROR"]
    error_counts = Counter(log["module"] for log in error_logs)
    return sorted(error_counts.items(), key=lambda item: item[1], reverse=True)

def create_level_filter(target_level: str) -> Callable[[dict], bool]:
    """
    Closure (замикання): повертає предикат, який запам'ятовує обраний
    рівень логування (target_level) для подальшої фільтрації списку.
    """
    normalized_target = target_level.upper()

    def predicate(log: dict) -> bool:
        return log.get("level", "").upper() == normalized_target

    return predicate

def aggregate_event_counts(*counters: Counter) -> Counter:
    """
    Демонстрація *args: об'єднує довільну кількість екземплярів Counter.
    """
    total = Counter()
    for c in counters:
        total.update(c)
    return total

def create_log_entry(**fields) -> dict:
    """
    Демонстрація **kwargs: створює новий запис логу з переданих іменованих аргументів.
    """
    return dict(fields)

def generate_summary_report(logs: list[dict]) -> dict:
    """Формує зведений аналітичний звіт щодо логів."""
    unique_levels = {log["level"] for log in logs}
    level_stats = Counter(log["level"] for log in logs)
    total_logs = len(logs)
    critical_logs = [log for log in logs if log["level"] == "CRITICAL"]

    return {
        "total_events": total_logs,
        "unique_levels": unique_levels,
        "level_breakdown": dict(level_stats),
        "critical_count": len(critical_logs),
        "error_ranking": rank_modules_by_errors(logs),
    }