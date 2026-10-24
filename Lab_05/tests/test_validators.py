"""Tests for validation and parsing of experiment records."""

import unittest

from experiment_importer.exceptions import RecordValidationError
from experiment_importer.models import ProcessingConfig
from experiment_importer.validators import parse_experiment


class TestValidators(unittest.TestCase):
    """Test parse_experiment validator against valid and invalid cases."""

    def setUp(self) -> None:
        self.config = ProcessingConfig(
            allowed_parameters=("temperature", "pressure", "voltage", "current"),
            min_result=0.0,
            max_result=1000.0,
            skip_invalid=True,
        )

    def test_parse_valid_row(self) -> None:
        row = {
            "experiment_id": "EXP-001",
            "name": "High Voltage Test",
            "researcher": "Dr. Frankov",
            "parameter": "voltage",
            "result": "220.5",
            "date": "2026-04-15",
        }
        record = parse_experiment(row, line_number=2, config=self.config)
        self.assertEqual(record.experiment_id, "EXP-001")
        self.assertEqual(record.name, "High Voltage Test")
        self.assertEqual(record.researcher, "Dr. Frankov")
        self.assertEqual(record.parameter, "voltage")
        self.assertEqual(record.result, 220.5)
        self.assertEqual(record.date, "2026-04-15")

    def test_empty_experiment_id(self) -> None:
        row = {
            "experiment_id": "   ",
            "name": "Test",
            "researcher": "Dr. Frankov",
            "parameter": "voltage",
            "result": "12.0",
            "date": "2026-04-15",
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_experiment(row, line_number=5, config=self.config)
        self.assertEqual(ctx.exception.field, "experiment_id")

    def test_disallowed_parameter(self) -> None:
        row = {
            "experiment_id": "EXP-002",
            "name": "Test",
            "researcher": "Dr. Frankov",
            "parameter": "radiation",  # not in setUp allowed_parameters
            "result": "12.0",
            "date": "2026-04-15",
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_experiment(row, line_number=6, config=self.config)
        self.assertEqual(ctx.exception.field, "parameter")

    def test_non_numeric_result(self) -> None:
        row = {
            "experiment_id": "EXP-003",
            "name": "Test",
            "researcher": "Dr. Frankov",
            "parameter": "pressure",
            "result": "invalid_float",
            "date": "2026-04-15",
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_experiment(row, line_number=7, config=self.config)
        self.assertEqual(ctx.exception.field, "result")
        self.assertIsNotNone(ctx.exception.__cause__)

    def test_out_of_range_result(self) -> None:
        row = {
            "experiment_id": "EXP-004",
            "name": "Test",
            "researcher": "Dr. Frankov",
            "parameter": "pressure",
            "result": "2500.0",  # max is 1000.0
            "date": "2026-04-15",
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_experiment(row, line_number=8, config=self.config)
        self.assertEqual(ctx.exception.field, "result")

    def test_invalid_date_format(self) -> None:
        row = {
            "experiment_id": "EXP-005",
            "name": "Test",
            "researcher": "Dr. Frankov",
            "parameter": "temperature",
            "result": "36.6",
            "date": "15/04/2026",  # Not ISO format
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_experiment(row, line_number=9, config=self.config)
        self.assertEqual(ctx.exception.field, "date")
        self.assertIsNotNone(ctx.exception.__cause__)


if __name__ == "__main__":
    unittest.main()
