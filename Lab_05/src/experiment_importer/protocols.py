"""Protocols and interfaces for extensible importer and exporter components."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Protocol

from experiment_importer.models import ExperimentRecord


class Importer(Protocol):
    """Protocol for data importers."""

    def read(self, path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
        """Read records from given path as a streaming iterator."""
        ...


class Exporter(Protocol):
    """Protocol for data exporters."""

    def export(self, records: Iterable[ExperimentRecord], path: Path) -> int:
        """Export records to target path atomically, returning exported count."""
        ...
