"""Tests for atomic JSON, JSON Lines, and summary exporters."""

import json
from pathlib import Path
import tempfile
import unittest

from experiment_importer.context_managers import atomic_write
from experiment_importer.exceptions import DataExportError
from experiment_importer.exporters import (
    export_experiments_json,
    export_experiments_jsonl,
    export_summary_json,
)
from experiment_importer.models import ExperimentRecord


class TestExporters(unittest.TestCase):
    """Test suite for atomic exporters."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.sample_records = [
            ExperimentRecord("EXP-1", "Alpha", "Dr. Frankov", "temperature", 295.1, "2026-02-01"),
            ExperimentRecord("EXP-2", "Beta", "Dr. Frankov", "pressure", 101.3, "2026-02-02"),
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_export_experiments_json(self) -> None:
        out_file = self.dir_path / "result.json"
        count = export_experiments_json(self.sample_records, out_file)
        self.assertEqual(count, 2)
        self.assertTrue(out_file.is_file())

        with out_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["experiment_id"], "EXP-1")
        self.assertEqual(data[1]["parameter"], "pressure")

    def test_export_experiments_jsonl(self) -> None:
        out_file = self.dir_path / "result.jsonl"
        count = export_experiments_jsonl(self.sample_records, out_file)
        self.assertEqual(count, 2)
        self.assertTrue(out_file.is_file())

        lines = [line.strip() for line in out_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        item1 = json.loads(lines[0])
        self.assertEqual(item1["experiment_id"], "EXP-1")

    def test_export_summary_json(self) -> None:
        summary_file = self.dir_path / "summary.json"
        summary_data = {"total": 10, "valid": 8, "invalid": 2}
        export_summary_json(summary_data, summary_file)
        self.assertTrue(summary_file.is_file())
        loaded = json.loads(summary_file.read_text(encoding="utf-8"))
        self.assertEqual(loaded["valid"], 8)

    def test_atomic_write_rollback_on_failure(self) -> None:
        target = self.dir_path / "atomic_target.txt"
        target.write_text("INITIAL DATA", encoding="utf-8")
        temp_file = target.with_suffix(target.suffix + ".tmp")

        with self.assertRaises(DataExportError):
            with atomic_write(target) as f:
                f.write("NEW PARTIAL DATA")
                raise RuntimeError("Simulated crash during write operation")

        # Target file content must remain unchanged
        self.assertEqual(target.read_text(encoding="utf-8"), "INITIAL DATA")
        # Temporary file must be removed
        self.assertFalse(temp_file.exists())


if __name__ == "__main__":
    unittest.main()
