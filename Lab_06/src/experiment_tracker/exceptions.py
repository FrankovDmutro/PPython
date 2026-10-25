"""Custom exceptions hierarchy for experiment tracker."""

from typing import Any


class ExperimentTrackerError(Exception):
    """Base exception for all domain errors."""


class ValidationError(ExperimentTrackerError):
    """Raised when an entity, parameter, or value fails validation."""

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        invalid_value: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.invalid_value = invalid_value

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f"field='{self.field}'")
        if self.invalid_value is not None:
            parts.append(f"value='{self.invalid_value}'")
        return " | ".join(parts)


class EmptySeriesError(ExperimentTrackerError):
    """Raised when statistical calculations are performed on an empty series."""


class EntityNotFoundError(ExperimentTrackerError):
    """Raised when a requested experiment or researcher is not found."""


class StorageError(ExperimentTrackerError):
    """Raised when repository or persistence operations fail."""


class SensorCommunicationError(ExperimentTrackerError):
    """Raised when reading from an asynchronous or external sensor fails."""


class ExportError(ExperimentTrackerError):
    """Raised when exporting experiments to file fails."""
