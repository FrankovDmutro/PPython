"""Custom exception hierarchy for the experiment importer application."""

from typing import Any


class ApplicationError(Exception):
    """Base exception for all application errors."""


class ConfigurationError(ApplicationError):
    """Raised when configuration file is missing, invalid, or violates schema."""


class DataError(ApplicationError):
    """Base exception for data processing errors."""


class DataImportError(DataError):
    """Raised when an input data source cannot be opened, read, or decoded."""


class RecordValidationError(DataError):
    """Raised when a specific data record fails validation."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
        raw_value: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line_number = line_number
        self.field = field
        self.raw_value = raw_value

    def __str__(self) -> str:
        parts: list[str] = [self.message]
        if self.line_number is not None:
            parts.append(f"line={self.line_number}")
        if self.field is not None:
            parts.append(f"field='{self.field}'")
        if self.raw_value is not None:
            parts.append(f"value='{self.raw_value}'")
        return " | ".join(parts)


class DataExportError(DataError):
    """Raised when data serialization or export cannot be completed."""
