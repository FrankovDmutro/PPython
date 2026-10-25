"""Tests for CSV import, JSON export, tmp_path isolation, and monkeypatch."""

import os
from pathlib import Path
import pytest

from experiment_tracker.exceptions import ExportError, ValidationError
from experiment_tracker.io import export_experiment_json, import_measurements_csv
from experiment_tracker.models import Experiment


@pytest.mark.unit
def test_import_measurements_csv_success(sample_csv_file: Path) -> None:
    """Test importing valid measurements CSV via fixture."""
    rows = import_measurements_csv(sample_csv_file)
    assert len(rows) == 2
    assert rows[0][0] == "EXP-F1"
    assert rows[0][1] == "Fixture Exp 1"
    assert rows[0][3] == "temperature"
    assert rows[0][4].value == pytest.approx(21.5)


@pytest.mark.unit
def test_import_measurements_csv_missing_file(tmp_path: Path) -> None:
    """Test FileNotFoundError for non-existent CSV."""
    absent = tmp_path / "absent.csv"
    with pytest.raises(FileNotFoundError):
        import_measurements_csv(absent)


@pytest.mark.unit
def test_import_measurements_csv_empty_header(tmp_path: Path) -> None:
    """Test ValidationError on empty CSV."""
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        import_measurements_csv(empty_file)
    assert exc_info.value.field == "header"


@pytest.mark.unit
def test_import_measurements_csv_invalid_field(tmp_path: Path) -> None:
    """Test ValidationError when row is missing required researcher field."""
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "experiment_id,title,researcher,department,parameter,unit,value,date\n"
        "EXP-1,Test Title,,Quantum,temperature,celsius,20.0,2026-04-01\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        import_measurements_csv(bad_csv)
    assert exc_info.value.field == "researcher"


@pytest.mark.unit
def test_export_experiment_json_success(tmp_path: Path, populated_experiment: Experiment) -> None:
    """Test exporting experiment to JSON in isolated tmp_path."""
    out_file = tmp_path / "exported.json"
    exported_path = export_experiment_json(populated_experiment, out_file)

    assert exported_path.is_file()
    assert "Cryogenic Thermal Expansion" in exported_path.read_text(encoding="utf-8")


@pytest.mark.unit
def test_export_experiment_json_error(populated_experiment: Experiment) -> None:
    """Test export failure raises ExportError when path is invalid."""
    invalid_path = Path("Z:/non_existent_drive/never_exists/out.json")
    with pytest.raises(ExportError):
        export_experiment_json(populated_experiment, invalid_path)


@pytest.mark.unit
def test_monkeypatch_environment_variable(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test using monkeypatch to dynamically set environment variable."""
    # Arrange
    monkeypatch.setenv("LAB_EXPERIMENT_MODE", "STRICT_AUDIT")
    monkeypatch.setenv("SENSOR_TIMEOUT_SEC", "15.5")

    # Act & Assert
    assert os.getenv("LAB_EXPERIMENT_MODE") == "STRICT_AUDIT"
    assert float(os.getenv("SENSOR_TIMEOUT_SEC", "0")) == pytest.approx(15.5)

    # Deletion test via monkeypatch
    monkeypatch.delenv("LAB_EXPERIMENT_MODE")
    assert os.getenv("LAB_EXPERIMENT_MODE") is None
