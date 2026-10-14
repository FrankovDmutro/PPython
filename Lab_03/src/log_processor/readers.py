from collections.abc import Iterator
from pathlib import Path


def read_lines(path: Path) -> Iterator[str]:
    """Потокове читання файлу без завантаження всього файлу в RAM."""
    with path.open("r", encoding="utf-8") as file:
        yield from file