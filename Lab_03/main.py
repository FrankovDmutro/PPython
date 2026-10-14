import csv
import time
import tracemalloc
from itertools import islice, takewhile
from pathlib import Path

from log_processor.analytics import calculate_log_summary, group_consecutive_levels
from log_processor.batches import batched_logs
from log_processor.filters import find_by_request_id
from log_processor.models import LogRecord, SimpleLogRangeIterator
from log_processor.pipeline import build_log_pipeline


def run_eager_pipeline(path: Path) -> dict:
    """Eager-версія: завантажує весь CSV в пам'ять перед аналізом."""
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    records = [
        LogRecord(
            timestamp=r["timestamp"],
            level=r["level"],
            module=r["module"],
            request_id=r["request_id"],
            message=r["message"].strip().capitalize(),
        )
        for r in rows
    ]

    error_records = [r for r in records if r.level == "ERROR"]
    return {
        "total": len(records),
        "errors": len(error_records),
    }


def run_lazy_pipeline(path: Path) -> dict:
    """Lazy-версія: створює генераторний конвеєр і споживає його в потоці."""
    pipeline = build_log_pipeline(path)
    summary = calculate_log_summary(pipeline)
    return summary


def measure_resource(func, *args) -> tuple[any, float, float]:
    """Вимірює час виконання та пікове використання оперативної пам'яті."""
    tracemalloc.start()
    start_time = time.perf_counter()

    result = func(*args)

    elapsed_time = time.perf_counter() - start_time
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_memory_mb = peak_memory / (1024 * 1024)
    return result, elapsed_time, peak_memory_mb


def main() -> None:
    data_path = Path("data/system_logs.csv")
    if not data_path.exists():
        print("Файл data/system_logs.csv не знайдено. Спочатку запустіть generate_data.py")
        return

    print("=== ДЕМОНСТРАЦІЯ ЗАВДАНЬ ВАРІАНТА 15 ===")

    # 1. Перші 5 помилок через islice
    error_pipeline = build_log_pipeline(data_path, level="ERROR")
    first_5_errors = list(islice(error_pipeline, 5))
    print(f"\n1. Перші {len(first_5_errors)} ERROR-записів (через islice):")
    for err in first_5_errors:
        print(f"  [{err.timestamp}] {err.module} ({err.request_id}): {err.message}")

    # 2. Потокова агрегація
    full_pipeline = build_log_pipeline(data_path)
    summary = calculate_log_summary(full_pipeline)
    print("\n2. Підрахунок рівнів логів (Streaming Summary):")
    for lvl, count in summary["level_counts"].items():
        print(f"  {lvl:<10}: {count}")

    # 3. Пакетна обробка
    auth_pipeline = build_log_pipeline(data_path, module="auth")
    first_batch = next(batched_logs(auth_pipeline, batch_size=3))
    print(f"\n3. Перший пакет (batch) для модуля 'auth' (розмір 3):")
    for item in first_batch:
        print(f"  {item.level} -> {item.message}")

    # 4. itertools.groupby: групування послідовних рівнів
    group_stream = islice(build_log_pipeline(data_path), 15)
    grouped = list(group_consecutive_levels(group_stream))
    print("\n4. Групування послідовних рівнів (перші 15 записів через groupby):")
    for lvl, cnt in grouped:
        print(f"  Послідовність рівнів {lvl}: {cnt} шт.")

    # 5. Пошук за request_id (early termination)
    test_id = first_5_errors[0].request_id
    search_pipeline = build_log_pipeline(data_path)
    found = find_by_request_id(search_pipeline, test_id)
    print(f"\n5. Пошук за request_id '{test_id}':")
    print(f"  Знайдено: {found}")

    # 6. Generator expression
    gen_pipeline = build_log_pipeline(data_path, level="CRITICAL")
    crit_messages = (rec.message for rec in gen_pipeline)
    print(f"\n6. Generator expression (перше критичне повідомлення): {next(crit_messages)}")

    print("\n=== ПОРІВНЯННЯ EAGER vs LAZY ===")
    _, eager_time, eager_mem = measure_resource(run_eager_pipeline, data_path)
    _, lazy_time, lazy_mem = measure_resource(run_lazy_pipeline, data_path)

    print(f"Eager: Час = {eager_time:.3f} с | Пікова пам'ять = {eager_mem:.2f} MB")
    print(f"Lazy:  Час = {lazy_time:.3f} с | Пікова пам'ять = {lazy_mem:.2f} MB")
    print(f"Економія пам'яті: у {(eager_mem / max(lazy_mem, 0.001)):.1f} разів менше використання RAM у Lazy версії.")

    # 7. Демонстрація власного Iterator-класу
    print("\n7. Власний iterator (SimpleLogRangeIterator):")
    custom_iter = SimpleLogRangeIterator(first_5_errors, stop=2)
    for rec in custom_iter:
        print(f"  [Власний ітератор] {rec.level}: {rec.message}")

    # 8. Демонстрація itertools.takewhile (3-й інструмент itertools)
    print("\n8. itertools.takewhile (читати логи до першого не-ERROR):")
    # беремо потік і дивимося скільки перших записів підряд мають рівень ERROR
    only_first_errors = list(takewhile(lambda r: r.level == "ERROR", build_log_pipeline(data_path)))
    print(f"  Знайдено підряд на початку файлу: {len(only_first_errors)} шт.")

if __name__ == "__main__":
    main()