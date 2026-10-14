import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_logs(path: Path, count: int = 150_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    levels = ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
    modules = ["auth", "database", "api", "payment", "worker"]
    messages = [
        "Connection established",
        "Slow query detected",
        "Connection refused to host",
        "Unhandled exception in service",
        "Request processed successfully",
        "Timeout while waiting for response",
    ]

    base_time = datetime(2026, 1, 1, 10, 0, 0)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "level", "module", "request_id", "message"])

        for i in range(1, count + 1):
            curr_time = (base_time + timedelta(seconds=i)).isoformat()
            writer.writerow([
                curr_time,
                random.choice(levels),
                random.choice(modules),
                f"req_{random.randint(1000, 9999)}",
                random.choice(messages),
            ])


if __name__ == "__main__":
    target = Path("data/system_logs.csv")
    print("Генерація тестового файлу логів...")
    generate_logs(target, 150_000)
    print(f"Файл згенеровано: {target}")