"""Tests for exception hierarchy and chaining."""

import unittest

from experiment_importer.exceptions import (
    ApplicationError,
    ConfigurationError,
    DataError,
    DataExportError,
    DataImportError,
    RecordValidationError,
)


class TestExceptions(unittest.TestCase):
    """Test custom exception classes, properties, and chaining."""

    def test_hierarchy(self) -> None:
        self.assertTrue(issubclass(ConfigurationError, ApplicationError))
        self.assertTrue(issubclass(DataError, ApplicationError))
        self.assertTrue(issubclass(DataImportError, DataError))
        self.assertTrue(issubclass(RecordValidationError, DataError))
        self.assertTrue(issubclass(DataExportError, DataError))

    def test_record_validation_error_str(self) -> None:
        err = RecordValidationError(
            "Invalid measurement result",
            line_number=42,
            field="result",
            raw_value="NaN",
        )
        self.assertEqual(err.line_number, 42)
        self.assertEqual(err.field, "result")
        self.assertEqual(err.raw_value, "NaN")
        msg = str(err)
        self.assertIn("Invalid measurement result", msg)
        self.assertIn("line=42", msg)
        self.assertIn("field='result'", msg)
        self.assertIn("value='NaN'", msg)

    def test_exception_chaining(self) -> None:
        cause = ValueError("invalid literal for float(): abc")
        try:
            try:
                raise cause
            except ValueError as val_err:
                raise RecordValidationError("Failed numeric conversion", line_number=10) from val_err
        except RecordValidationError as custom_err:
            self.assertIs(custom_err.__cause__, cause)


if __name__ == "__main__":
    unittest.main()
