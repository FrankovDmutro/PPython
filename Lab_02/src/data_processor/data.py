# Незмінні налаштування сесії аналізу логів (tuple)
APP_METADATA: tuple[str, str, str] = ("OrderService", "Production", "v2.4.1")

# Набір структурованих лог-записів (list of dicts)
LOG_RECORDS: list[dict] = [
    {
        "timestamp": "2026-10-07T10:15:30",
        "level": "INFO",
        "module": "auth",
        "message": "User admin successfully logged in",
        "request_id": "req-101",
    },
    {
        "timestamp": "2026-10-07T10:16:05",
        "level": "ERROR",
        "module": "database",
        "message": "Connection timeout to replica pool",
        "request_id": "req-102",
    },
    {
        "timestamp": "2026-10-07T10:16:40",
        "level": "WARNING",
        "module": "payment",
        "message": "Gateway response delayed by 1200ms",
        "request_id": "req-103",
    },
    {
        "timestamp": "2026-10-07T10:17:12",
        "level": "ERROR",
        "module": "payment",
        "message": "Card verification signature mismatch",
        "request_id": "req-104",
    },
    {
        "timestamp": "2026-10-07T10:18:00",
        "level": "INFO",
        "module": "database",
        "message": "Auto-vacuum worker completed task",
        "request_id": "req-105",
    },
    {
        "timestamp": "2026-10-07T10:18:25",
        "level": "ERROR",
        "module": "payment",
        "message": "Insufficient funds on merchant account",
        "request_id": "req-106",
    },
    {
        "timestamp": "2026-10-07T10:19:10",
        "level": "DEBUG",
        "module": "auth",
        "message": "Token refresh payload evaluated",
        "request_id": "req-107",
    },
    {
        "timestamp": "2026-10-07T10:20:00",
        "level": "CRITICAL",
        "module": "kernel",
        "message": "Out of memory event signaled by system",
        "request_id": "req-108",
    },
]