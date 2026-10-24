"""Domain models and configuration models for the experiment importer system."""

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    """Domain model representing a single scientific experiment measurement.

    Variant 15 specification:
    - experiment_id: unique identifier
    - name: descriptive title of experiment
    - researcher: person responsible for measurement
    - parameter: measured physical parameter (e.g. temperature, pressure)
    - result: numeric measurement value
    - date: ISO date string (YYYY-MM-DD)
    """

    experiment_id: str
    name: str
    researcher: str
    parameter: str
    result: float
    date: str

    def to_dict(self) -> dict[str, object]:
        """Convert record to JSON-serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Processing and validation rules."""

    allowed_parameters: tuple[str, ...]
    min_result: float
    max_result: float
    skip_invalid: bool


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Logging settings."""

    level: str
    path: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Root application configuration."""

    input_path: Path
    output_path: Path
    summary_path: Path
    processing: ProcessingConfig
    logging: LoggingConfig
