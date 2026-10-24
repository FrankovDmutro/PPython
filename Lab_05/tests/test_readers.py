"""Tests for streaming CSV reader."""

from pathlib import Path
import tempfile
import unittest

from experiment_importer.exceptions import DataImportError
from experiment_importer.readers import read_csv_rows


class TestReaders(unittest.TestCase):
    """Test suite for streaming readers."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_read_valid_csv(self) -> None:
        csv_file = self.dir_path / "valid.csv"
        csv_file.write_text(
            "experiment_id,name,researcher,parameter,result,date\n"
            "EXP-1,Test 1,Dr. Frankov,temperature,300.0,2026-01-01\n"
            "EXP-2,Test 2,Dr. Frankov,pressure,100.0,2026-01-02\n",
            encoding="utf-8",
        )
        rows = list(read_csv_rows(csv_file))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 2)  # line number 2
        self.assertEqual(rows[0][1]["experiment_id"], "EXP-1")
        self.assertEqual(rows[1][0], 3)  # line number 3
        self.assertEqual(rows[1][1]["experiment_id"], "EXP-2")

    def test_file_not_found(self) -> None:
        non_existent = self.dir_path / "missing.csv"
        with self.assertRaises(DataImportError) as ctx:
            list(read_csv_rows(non_existent))
        self.assertIn("not found", str(ctx.exception).lower())

    def test_streaming_generator_is_lazy(self) -> None:
        csv_file = self.dir_path / "lazy.csv"
        csv_file.write_text(
            "experiment_id,name,researcher,parameter,result,date\n"
            "EXP-1,Test 1,Dr. Frankov,temperature,300.0,2026-01-01\n"
            "EXP-2,Test 2,Dr. Frankov,pressure,100.0,2026-01-02\n",
            encoding="utf-8",
        )
        gen = read_csv_rows(csv_file)
        # Advance only first row
        first_line_num, first_row = next(gen)
        self.assertEqual(first_line_num, 2)
        self.assertEqual(first_row["experiment_id"], "EXP-1")


if __name__ == "__main__":
    unittest.main()
