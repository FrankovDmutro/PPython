"""Unit and integration tests for ExperimentService using Mock, return_value, side_effect, and interaction assertions."""

from pathlib import Path
from unittest.mock import Mock
import pytest

from experiment_tracker.exceptions import (
    EntityNotFoundError,
    ExportError,
    StorageError,
    ValidationError,
)
from experiment_tracker.models import Experiment, Measurement, Researcher
from experiment_tracker.repository import ExperimentRepository, InMemoryExperimentRepository
from experiment_tracker.services import (
    AnalysisStrategy,
    ExperimentService,
    Exporter,
    StatisticalAnalysisStrategy,
)


@pytest.mark.unit
def test_create_experiment_calls_repository_save(sample_researcher: Researcher) -> None:
    """Test experiment creation with Mock repository interaction assertion."""
    # Arrange
    mock_repo = Mock(spec=ExperimentRepository)
    service = ExperimentService(mock_repo)

    # Act
    created = service.create_experiment(
        experiment_id="EXP-MOCK-1",
        title="Superconductivity Test",
        researcher=sample_researcher,
        parameter="temperature",
    )

    # Assert
    assert created.id == "EXP-MOCK-1"
    mock_repo.save.assert_called_once_with(created)


@pytest.mark.unit
def test_create_experiment_invalid_title_does_not_call_repository(sample_researcher: Researcher) -> None:
    """Test validation failure prevents repository interaction."""
    # Arrange
    mock_repo = Mock(spec=ExperimentRepository)
    service = ExperimentService(mock_repo)

    # Act & Assert
    with pytest.raises(ValidationError):
        service.create_experiment(
            experiment_id="EXP-ERR",
            title="   ",  # Invalid empty title
            researcher=sample_researcher,
            parameter="temperature",
        )

    # Interaction assertion: save must NOT be called
    mock_repo.save.assert_not_called()


@pytest.mark.unit
def test_get_experiment_return_value_and_missing(sample_experiment: Experiment) -> None:
    """Test get_experiment with configured return_value and EntityNotFoundError on missing."""
    mock_repo = Mock(spec=ExperimentRepository)
    # Configure return_value
    mock_repo.get.return_value = sample_experiment

    service = ExperimentService(mock_repo)
    result = service.get_experiment(sample_experiment.id)

    assert result == sample_experiment
    mock_repo.get.assert_called_once_with(sample_experiment.id)

    # Now simulate non-existent entity
    mock_repo.get.return_value = None
    with pytest.raises(EntityNotFoundError):
        service.get_experiment("NON_EXISTENT")


@pytest.mark.unit
def test_export_experiment_failure_path_with_side_effect(tmp_path: Path, sample_experiment: Experiment) -> None:
    """Test failure path using side_effect on mock Exporter."""
    mock_repo = Mock(spec=ExperimentRepository)
    mock_repo.get.return_value = sample_experiment

    mock_exporter = Mock(spec=Exporter)
    # Configure side_effect to simulate I/O disk failure
    mock_exporter.export.side_effect = ExportError("Disk write failed: Read-only filesystem")

    service = ExperimentService(repository=mock_repo, exporter=mock_exporter)
    dest = tmp_path / "failed_out.json"

    with pytest.raises(ExportError) as exc_info:
        service.export_experiment(sample_experiment.id, dest)

    assert "Read-only filesystem" in str(exc_info.value)
    mock_exporter.export.assert_called_once_with(sample_experiment, dest)


@pytest.mark.integration
def test_experiment_service_full_lifecycle_integration(tmp_path: Path, sample_researcher: Researcher) -> None:
    """Integration test verifying complete flow: creation, measurements, analysis, and atomic export."""
    # Real fake repository and real analysis strategy
    repo = InMemoryExperimentRepository()
    service = ExperimentService(repository=repo, analysis_strategy=StatisticalAnalysisStrategy())

    # 1. Create experiment
    exp = service.create_experiment(
        experiment_id="INT-EXP-01",
        title="High Precision Calibration",
        researcher=sample_researcher,
        parameter="pressure",
    )

    # 2. Record measurements
    service.record_measurement(exp.id, value=100000.0, unit="pascal", timestamp="2026-04-10")
    service.record_measurement(exp.id, value=101000.0, unit="pascal", timestamp="2026-04-11")
    service.record_measurement(exp.id, value=102000.0, unit="pascal", timestamp="2026-04-12")

    # 3. Analyze
    summary = service.analyze_experiment(exp.id)
    assert summary["measurements_count"] == 3
    assert summary["average"] == pytest.approx(101000.0)
    assert summary["min"] == pytest.approx(100000.0)
    assert summary["max"] == pytest.approx(102000.0)

    # 4. Export to file
    out_file = tmp_path / "integration_export.json"
    exported_path = service.export_experiment(exp.id, out_file)
    assert exported_path.is_file()
    assert exported_path.stat().st_size > 0

    # 5. Search by researcher
    found = service.search_by_researcher("Dr. Frankov")
    assert len(found) == 1
    assert found[0].id == exp.id


@pytest.mark.unit
def test_statistical_analysis_empty_experiment(sample_experiment: Experiment) -> None:
    """Test statistical analysis strategy handles empty experiment gracefully."""
    strategy = StatisticalAnalysisStrategy()
    summary = strategy.compute_summary(sample_experiment)
    assert summary["measurements_count"] == 0
    assert summary["average"] == 0.0

