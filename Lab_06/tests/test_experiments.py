"""Executable laboratory experiments corresponding to sections 84-90 of the manual.

Experiment 1: Weak vs strong tests (execution != verification)
Experiment 2: Coverage without assertions
Experiment 3: Branch coverage (partial branches vs 100% branch coverage)
Experiment 4: Mock vs fake comparison
Experiment 5: Flaky test vs deterministic test
Experiment 6: tmp_path isolation
Experiment 7: Failure path testing (return_value vs side_effect)
"""

from pathlib import Path
import random
import time
from unittest.mock import Mock
import pytest

from experiment_tracker.exceptions import ExportError, StorageError
from experiment_tracker.models import Experiment, Measurement, Researcher
from experiment_tracker.repository import ExperimentRepository, InMemoryExperimentRepository
from experiment_tracker.services import ExperimentService, Exporter


# Helper functions for experiments
def calculate_calibrated_value(raw: float, factor: float) -> float:
    """Production function to calibrate sensor readings."""
    return (raw * factor) + 1.25


def classify_experiment_result(result: float) -> str:
    """Function with branches to test branch coverage."""
    if result >= 90.0:
        return "optimal"
    if result >= 60.0:
        return "acceptable"
    return "critical"


# ==================== EXPERIMENT 1: WEAK VS STRONG ====================
@pytest.mark.experiment
def test_experiment_1_weak() -> None:
    """Weak test: executes production code but asserts nothing.

    Test passes even if the function has a bug or returns nonsense.
    Conclusion: execution != verification.
    """
    calculate_calibrated_value(10.0, 2.0)


@pytest.mark.experiment
def test_experiment_1_strong() -> None:
    """Strong test: strictly asserts exact calculated value with pytest.approx."""
    result = calculate_calibrated_value(10.0, 2.0)
    assert result == pytest.approx(21.25)


# ==================== EXPERIMENT 2: COVERAGE WITHOUT ASSERTIONS ====================
@pytest.mark.experiment
def test_experiment_2_coverage_without_assertions() -> None:
    """Demonstrates high statement coverage without meaningful verification.

    Even if calculate_calibrated_value had an internal logical bug,
    a test without assert still marks all lines as covered.
    """
    res = calculate_calibrated_value(100.0, 1.5)
    # Weak assertion only checks type, not correctness
    assert isinstance(res, float)


@pytest.mark.experiment
def test_experiment_2_meaningful_assertions() -> None:
    """Meaningful verification ensuring both domain invariants and exact math."""
    res = calculate_calibrated_value(100.0, 1.5)
    # Expected: (100.0 * 1.5) + 1.25 = 151.25
    assert res == pytest.approx(151.25)
    assert res > 100.0


# ==================== EXPERIMENT 3: BRANCH COVERAGE ====================
@pytest.mark.experiment
def test_experiment_3_partial_branches() -> None:
    """Covers only first two branches (optimal, acceptable), missing critical branch."""
    assert classify_experiment_result(95.0) == "optimal"
    assert classify_experiment_result(70.0) == "acceptable"


@pytest.mark.experiment
def test_experiment_3_complete_branch_coverage() -> None:
    """Provides 100% branch coverage by testing all 3 branches."""
    assert classify_experiment_result(95.0) == "optimal"
    assert classify_experiment_result(70.0) == "acceptable"
    assert classify_experiment_result(40.0) == "critical"


# ==================== EXPERIMENT 4: MOCK VS FAKE ====================
@pytest.mark.experiment
def test_experiment_4_mock_interaction(sample_researcher: Researcher) -> None:
    """Testing with Mock: focuses on interaction (methods called, arguments)."""
    mock_repo = Mock(spec=ExperimentRepository)
    service = ExperimentService(mock_repo)

    exp = service.create_experiment("MOCK-01", "Mock Title", sample_researcher, "temperature")

    # Mock verifies interaction
    mock_repo.save.assert_called_once_with(exp)


@pytest.mark.experiment
def test_experiment_4_fake_state(sample_researcher: Researcher) -> None:
    """Testing with Fake: focuses on real state changes and repository behavior."""
    fake_repo = InMemoryExperimentRepository()
    service = ExperimentService(fake_repo)

    exp = service.create_experiment("FAKE-01", "Fake Title", sample_researcher, "temperature")

    # Fake verifies state in storage
    stored = fake_repo.get("FAKE-01")
    assert stored is not None
    assert stored.title == "Fake Title"


# ==================== EXPERIMENT 5: FLAKY VS DETERMINISTIC ====================
@pytest.mark.experiment
def test_experiment_5_flaky_concept(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulates converting a non-deterministic flaky test into a deterministic test."""
    # Flaky version would do: assert random.choice([True, False]) == True
    # Deterministic version controls randomness via monkeypatch:
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    result = random.choice([True, False])
    assert result is True


# ==================== EXPERIMENT 6: TMP_PATH ISOLATION ====================
@pytest.mark.experiment
def test_experiment_6_tmp_path_isolation(tmp_path: Path) -> None:
    """Verifies that pytest tmp_path provides an isolated unique sandbox."""
    file_a = tmp_path / "sandbox_test.txt"
    file_a.write_text("ISOLATED_DATA_RUN_1", encoding="utf-8")

    assert file_a.is_file()
    assert file_a.read_text(encoding="utf-8") == "ISOLATED_DATA_RUN_1"
    # Ensure it resides in operating system temp folder, not git repo
    assert "AppData" in str(tmp_path) or "temp" in str(tmp_path).lower() or "tmp" in str(tmp_path).lower()


# ==================== EXPERIMENT 7: FAILURE PATH TESTING ====================
@pytest.mark.experiment
def test_experiment_7_failure_path_side_effect(sample_experiment: Experiment, tmp_path: Path) -> None:
    """Verifies dependency failure handling using side_effect and absence of unexpected interactions."""
    mock_repo = Mock(spec=ExperimentRepository)
    mock_repo.get.return_value = sample_experiment

    mock_exporter = Mock(spec=Exporter)
    # Simulate network/storage catastrophic outage
    mock_exporter.export.side_effect = ExportError("Critical NAS Outage: Connection refused")

    service = ExperimentService(mock_repo, exporter=mock_exporter)
    dest = tmp_path / "never_created.json"

    with pytest.raises(ExportError) as exc_info:
        service.export_experiment(sample_experiment.id, dest)

    assert "Critical NAS Outage" in str(exc_info.value)
    # Verify export was attempted once
    mock_exporter.export.assert_called_once_with(sample_experiment, dest)
    # Verify repository was NOT deleted or corrupted
    mock_repo.delete.assert_not_called()
