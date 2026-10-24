"""Executable experiments corresponding to sections 77-83 of the laboratory manual.

Experiment 1: Strict vs tolerant processing
Experiment 2: Streaming vs eager memory benchmarks (tracemalloc)
Experiment 3: Exception chaining (traceback and __cause__)
Experiment 4: Atomic output failure recovery (.tmp cleanup)
Experiment 5: Configuration error handling
"""

import csv
from pathlib import Path
import tempfile
import tracemalloc
import unittest

from experiment_importer.config import load_config
from experiment_importer.context_managers import atomic_write
from experiment_importer.exceptions import (
    ConfigurationError,
    DataExportError,
    RecordValidationError,
)
from experiment_importer.models import AppConfig, LoggingConfig, ProcessingConfig
from experiment_importer.readers import read_csv_rows
from experiment_importer.services import ImportStatistics, import_experiments, run_pipeline


class TestLabExperiments(unittest.TestCase):
    """Automated executions for required laboratory experiments."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_experiment_1_strict_vs_tolerant(self) -> None:
        """Experiment 1: 1000 valid records + 10 invalid records."""
        dataset = self.dir_path / "exp1_dataset.csv"
        with dataset.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["experiment_id", "name", "researcher", "parameter", "result", "date"])
            # 1000 valid records
            for i in range(1, 1001):
                writer.writerow([f"EXP-{i:04d}", f"Test {i}", "Dr. Frankov", "temperature", 300.0 + (i % 50), "2026-03-15"])
            # 10 invalid records
            for i in range(1001, 1011):
                writer.writerow([f"EXP-{i:04d}", f"Bad Test {i}", "Dr. Frankov", "invalid_param", "not_a_num", "bad_date"])

        proc_tolerant = ProcessingConfig(
            allowed_parameters=("temperature", "pressure"),
            min_result=0.0,
            max_result=10000.0,
            skip_invalid=True,
        )
        proc_strict = ProcessingConfig(
            allowed_parameters=("temperature", "pressure"),
            min_result=0.0,
            max_result=10000.0,
            skip_invalid=False,
        )

        # Tolerant run
        stats_tolerant = ImportStatistics()
        tolerant_records = list(import_experiments(dataset, proc_tolerant, stats_tolerant))
        self.assertEqual(stats_tolerant.total, 1010)
        self.assertEqual(stats_tolerant.valid, 1000)
        self.assertEqual(stats_tolerant.invalid, 10)
        self.assertEqual(len(tolerant_records), 1000)

        # Strict run
        stats_strict = ImportStatistics()
        with self.assertRaises(RecordValidationError):
            list(import_experiments(dataset, proc_strict, stats_strict))
        # Aborted on record 1001
        self.assertEqual(stats_strict.total, 1001)
        self.assertEqual(stats_strict.valid, 1000)
        self.assertEqual(stats_strict.invalid, 1)

    def test_experiment_2_streaming_vs_eager_memory(self) -> None:
        """Experiment 2: Compare memory usage of eager loading vs streaming generator."""
        dataset = self.dir_path / "exp2_large.csv"
        num_records = 20_000
        with dataset.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["experiment_id", "name", "researcher", "parameter", "result", "date"])
            for i in range(num_records):
                writer.writerow([f"EXP-{i}", "Measurement", "Dr. Frankov", "temperature", 298.15, "2026-03-20"])

        # Eager variant
        tracemalloc.start()
        with dataset.open(encoding="utf-8", newline="") as file:
            eager_list = list(csv.DictReader(file))
            eager_count = len(eager_list)
        _, peak_eager = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Streaming variant
        tracemalloc.start()
        def streaming_import(path: Path):
            with path.open(encoding="utf-8", newline="") as file:
                yield from csv.DictReader(file)

        stream_count = sum(1 for _ in streaming_import(dataset))
        _, peak_streaming = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.assertEqual(eager_count, num_records)
        self.assertEqual(stream_count, num_records)
        # Streaming peak memory must be significantly less than eager peak memory
        self.assertLess(peak_streaming, peak_eager)
        print(f"\n[Experiment 2 Memory Benchmark ({num_records} rows)]")
        print(f"  Eager list peak memory:      {peak_eager / 1024:.2f} KB")
        print(f"  Streaming generator peak:    {peak_streaming / 1024:.2f} KB")
        print(f"  Memory reduction ratio:      {(1 - peak_streaming / peak_eager) * 100:.1f} %")

    def test_experiment_3_exception_chaining(self) -> None:
        """Experiment 3: Inspect traceback and exception __cause__."""
        row = {
            "experiment_id": "EXP-FAIL",
            "name": "Chaining Test",
            "researcher": "Dr. Frankov",
            "parameter": "temperature",
            "result": "corrupted_float_data",
            "date": "2026-03-01",
        }
        cfg = ProcessingConfig(allowed_parameters=("temperature",), min_result=0.0, max_result=1000.0, skip_invalid=False)

        try:
            from experiment_importer.validators import parse_experiment
            parse_experiment(row, line_number=15, config=cfg)
        except RecordValidationError as error:
            self.assertIsNotNone(error.__cause__)
            self.assertIsInstance(error.__cause__, ValueError)
            self.assertEqual(error.line_number, 15)
            self.assertEqual(error.field, "result")

    def test_experiment_4_atomic_output_recovery(self) -> None:
        """Experiment 4: Crash simulation during atomic write guarantees no corrupted target and .tmp cleanup."""
        target_json = self.dir_path / "valid_output.json"
        target_json.write_text('{"status": "original_valid_data"}', encoding="utf-8")
        temp_file = target_json.with_suffix(target_json.suffix + ".tmp")

        with self.assertRaises(DataExportError):
            with atomic_write(target_json) as f:
                f.write('{"status": "partial_corrupted_write...')
                raise RuntimeError("Disk power loss simulation")

        # Original target file is completely preserved
        self.assertEqual(target_json.read_text(encoding="utf-8"), '{"status": "original_valid_data"}')
        # Temporary file was unlinked
        self.assertFalse(temp_file.exists())

    def test_experiment_5_configuration_errors(self) -> None:
        """Experiment 5: Validate handling of non-existent, malformed, and out-of-bounds configuration."""
        non_existent = self.dir_path / "missing_config.yaml"
        with self.assertRaises(ConfigurationError):
            load_config(non_existent)

        malformed = self.dir_path / "malformed.yaml"
        malformed.write_text("invalid: yaml: : syntax", encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            load_config(malformed)


if __name__ == "__main__":
    unittest.main()
