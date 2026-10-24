"""Tests for service pipeline, filtering, and statistics aggregation."""

from pathlib import Path
import tempfile
import unittest

from experiment_importer.exceptions import RecordValidationError
from experiment_importer.models import AppConfig, LoggingConfig, ProcessingConfig
from experiment_importer.services import (
    ImportStatistics,
    filter_by_parameter,
    import_experiments,
    run_pipeline,
)


class TestServices(unittest.TestCase):
    """Test suite for pipeline, filtering, and statistics."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.csv_file = self.dir_path / "data.csv"
        self.csv_file.write_text(
            "experiment_id,name,researcher,parameter,result,date\n"
            "EXP-1,Test 1,Dr. Frankov,temperature,298.15,2026-03-01\n"
            "EXP-2,Test 2,Dr. Alan,forbidden_param,10.0,2026-03-02\n"
            "EXP-3,Test 3,Dr. Frankov,temperature,310.0,2026-03-03\n",
            encoding="utf-8",
        )
        self.proc_config = ProcessingConfig(
            allowed_parameters=("temperature", "pressure"),
            min_result=0.0,
            max_result=1000.0,
            skip_invalid=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_import_tolerant_mode(self) -> None:
        stats = ImportStatistics()
        records = list(import_experiments(self.csv_file, self.proc_config, stats))
        self.assertEqual(len(records), 2)
        self.assertEqual(stats.total, 3)
        self.assertEqual(stats.valid, 2)
        self.assertEqual(stats.invalid, 1)
        self.assertEqual(len(stats.errors), 1)
        self.assertEqual(stats.errors[0]["field"], "parameter")

    def test_import_strict_mode(self) -> None:
        strict_config = ProcessingConfig(
            allowed_parameters=("temperature", "pressure"),
            min_result=0.0,
            max_result=1000.0,
            skip_invalid=False,
        )
        stats = ImportStatistics()
        with self.assertRaises(RecordValidationError):
            list(import_experiments(self.csv_file, strict_config, stats))
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.valid, 1)
        self.assertEqual(stats.invalid, 1)

    def test_filter_by_parameter(self) -> None:
        stats = ImportStatistics()
        records = import_experiments(self.csv_file, self.proc_config, stats)
        filtered = list(filter_by_parameter(records, "temperature"))
        self.assertEqual(len(filtered), 2)
        for r in filtered:
            self.assertEqual(r.parameter, "temperature")

    def test_run_pipeline_end_to_end(self) -> None:
        out_json = self.dir_path / "out.json"
        out_summary = self.dir_path / "summary.json"
        app_cfg = AppConfig(
            input_path=self.csv_file,
            output_path=out_json,
            summary_path=out_summary,
            processing=self.proc_config,
            logging=LoggingConfig(level="INFO", path=self.dir_path / "app.log"),
        )
        count, stats = run_pipeline(app_cfg)
        self.assertEqual(count, 2)
        self.assertEqual(stats.valid, 2)
        self.assertTrue(out_json.is_file())
        self.assertTrue(out_summary.is_file())


if __name__ == "__main__":
    unittest.main()
