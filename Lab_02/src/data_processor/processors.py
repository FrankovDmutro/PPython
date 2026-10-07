from collections import Counter, defaultdict

def get_unique_log_levels(logs: list[dict]) -> set[str]:
    """Повертає множину унікальних рівнів логування (Set comprehension)."""
    return {log["level"] for log in logs}

def build_request_index(logs: list[dict]) -> dict[str, dict]:
    """Створює словниковий індекс за request_id для пошуку за O(1) (Dict comprehension)."""
    return {log["request_id"]: log for log in logs}

def group_logs_by_module(logs: list[dict]) -> dict[str, list[dict]]:
    """Групує записи за модулем за допомогою defaultdict."""
    grouped = defaultdict(list)
    for log in logs:
        grouped[log["module"]].append(log)
    return dict(grouped)

def count_events_by_level(logs: list[dict]) -> Counter:
    """Підраховує кількість подій для кожного рівня логування (Counter)."""
    return Counter(log["level"] for log in logs)

def filter_error_events(logs: list[dict]) -> list[dict]:
    """Фільтрує записи, залишаючи виключно події рівня ERROR (List comprehension)."""
    return [log for log in logs if log["level"] == "ERROR"]