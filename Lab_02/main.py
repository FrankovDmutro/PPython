from src.data_processor.data import LOG_RECORDS, APP_METADATA
from src.data_processor.processors import (
    get_unique_log_levels,
    build_request_index,
    group_logs_by_module,
    count_events_by_level,
    filter_error_events,
)
from src.data_processor.analytics import (
    calculate_error_rate,
    rank_modules_by_errors,
    create_level_filter,
    aggregate_event_counts,
    create_log_entry,
    generate_summary_report,
)

def print_separator(title: str):
    print(f"\n{'=' * 15} {title} {'=' * 15}")

def main():
    print_separator(f"СИСТЕМА: {APP_METADATA[0]} ({APP_METADATA[1]}, {APP_METADATA[2]})")

    # 1. Унікальні рівні (set comprehension)
    levels = get_unique_log_levels(LOG_RECORDS)
    print(f"1. Унікальні рівні логування (set): {levels}")

    # 2. Підрахунок подій за рівнями (Counter)
    level_counts = count_events_by_level(LOG_RECORDS)
    print(f"2. Кількість подій за рівнями (Counter): {dict(level_counts)}")

    # 3. Групування за модулями (defaultdict)
    grouped_by_module = group_logs_by_module(LOG_RECORDS)
    print("3. Групування за модулями:")
    for mod, entries in grouped_by_module.items():
        print(f"   - {mod:<10}: {len(entries)} подій")

    # 4. Фільтрація тільки ERROR events (list comprehension)
    error_events = filter_error_events(LOG_RECORDS)
    print(f"\n4. Події рівня ERROR ({len(error_events)} шт.):")
    for err in error_events:
        print(f"   [{err['timestamp']}] {err['module']}: {err['message']} ({err['request_id']})")

    # 5. Швидкий пошук за request_id через індекс (dict comprehension)
    request_index = build_request_index(LOG_RECORDS)
    target_req_id = "req-104"
    found_log = request_index.get(target_req_id)
    print(f"\n5. Результат пошуку за {target_req_id} у dict-індексі: {found_log}")

    # 6. Рейтинг модулів за кількістю помилок (lambda sorting)
    ranking = rank_modules_by_errors(LOG_RECORDS)
    print(f"\n6. Рейтинг модулів за кількістю помилок: {ranking}")

    # 7. Демонстрація Closure (замикання) для довільного рівня
    warning_filter = create_level_filter("WARNING")
    warning_logs = [log for log in LOG_RECORDS if warning_filter(log)]
    print(f"\n7. Фільтрація через Closure (рівень WARNING): {len(warning_logs)} запис(ів)")

    # 8. Декоратор та обчислення відсотка помилок
    err_rate = calculate_error_rate(LOG_RECORDS)
    print(f"8. Частка збійних подій (ERROR + CRITICAL): {err_rate:.2f}%")

    # 9. Демонстрація *args та **kwargs
    c1 = count_events_by_level(LOG_RECORDS[:4])
    c2 = count_events_by_level(LOG_RECORDS[4:])
    aggregated = aggregate_event_counts(c1, c2)
    print(f"\n9. Агрегація двох Counter (*args): {dict(aggregated)}")

    new_log = create_log_entry(
        timestamp="2026-10-07T10:21:00",
        level="INFO",
        module="audit",
        message="Compliance check passed",
        request_id="req-109",
    )
    print(f"   Створення запису через **kwargs: {new_log['module']} -> {new_log['message']}")

    # 10. Формування підсумкового звіту
    summary = generate_summary_report(LOG_RECORDS)
    print_separator("ПІДСУМКОВИЙ ЗВІТ (SUMMARY REPORT)")
    for key, value in summary.items():
        print(f"  {key:<18}: {value}")

if __name__ == "__main__":
    main()