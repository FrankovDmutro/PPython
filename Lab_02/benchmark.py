import time
import random

def run_benchmark():
    sizes = [1_000, 10_000, 100_000]
    print(f"{'Кількість записів':<18} | {'list search (с)':<18} | {'dict search (с)':<18}")
    print("-" * 60)

    for n in sizes:
        # Генерація синтетичних логів
        mock_logs = [
            {
                "timestamp": f"2026-10-07T10:{i % 60:02d}:00",
                "level": random.choice(["INFO", "WARNING", "ERROR", "DEBUG"]),
                "module": random.choice(["auth", "db", "api", "payment"]),
                "message": f"Message body {i}",
                "request_id": f"req-{i}",
            }
            for i in range(n)
        ]

        # Найгірший випадок: шукаємо останній елемент
        target_id = f"req-{n - 1}"

        # 1. Пошук у list: O(n)
        start = time.perf_counter()
        _ = next((item for item in mock_logs if item["request_id"] == target_id), None)
        list_time = time.perf_counter() - start

        # 2. Пошук у dict: O(1)
        index = {item["request_id"]: item for item in mock_logs}
        start = time.perf_counter()
        _ = index.get(target_id)
        dict_time = time.perf_counter() - start

        print(f"{n:<18} | {list_time:<18.8f} | {dict_time:<18.8f}")

if __name__ == "__main__":
    run_benchmark()