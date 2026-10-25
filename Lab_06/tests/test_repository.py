"""Unit tests for experiment repository implementation."""

import pytest

from experiment_tracker.exceptions import StorageError
from experiment_tracker.models import Experiment, Researcher
from experiment_tracker.repository import InMemoryExperimentRepository


@pytest.mark.unit
def test_repository_save_and_get(in_memory_repo: InMemoryExperimentRepository, sample_experiment: Experiment) -> None:
    """Test saving and retrieving experiment."""
    in_memory_repo.save(sample_experiment)
    retrieved = in_memory_repo.get(sample_experiment.id)

    assert retrieved is not None
    assert retrieved.id == sample_experiment.id
    assert retrieved.title == sample_experiment.title


@pytest.mark.unit
def test_repository_get_non_existent(in_memory_repo: InMemoryExperimentRepository) -> None:
    """Test retrieving non-existent experiment returns None."""
    assert in_memory_repo.get("ABSENT_ID") is None


@pytest.mark.unit
def test_repository_find_by_researcher(in_memory_repo: InMemoryExperimentRepository, sample_researcher: Researcher) -> None:
    """Test searching experiments by researcher name."""
    exp1 = Experiment("E1", "Exp 1", sample_researcher, "temperature")
    exp2 = Experiment("E2", "Exp 2", sample_researcher, "voltage")
    other_res = Researcher("R2", "Dr. Alan", "Physics")
    exp3 = Experiment("E3", "Exp 3", other_res, "current")

    in_memory_repo.save(exp1)
    in_memory_repo.save(exp2)
    in_memory_repo.save(exp3)

    found = in_memory_repo.find_by_researcher("Dr. Frankov")
    assert len(found) == 2
    assert {e.id for e in found} == {"E1", "E2"}


@pytest.mark.unit
def test_repository_delete(in_memory_repo: InMemoryExperimentRepository, sample_experiment: Experiment) -> None:
    """Test deleting experiment."""
    in_memory_repo.save(sample_experiment)
    assert in_memory_repo.delete(sample_experiment.id) is True
    assert in_memory_repo.get(sample_experiment.id) is None
    assert in_memory_repo.delete(sample_experiment.id) is False


@pytest.mark.unit
def test_repository_simulated_failure(in_memory_repo: InMemoryExperimentRepository, sample_experiment: Experiment) -> None:
    """Test repository error handling when storage failure occurs."""
    in_memory_repo.simulate_failure = True
    with pytest.raises(StorageError):
        in_memory_repo.save(sample_experiment)
    with pytest.raises(StorageError):
        in_memory_repo.list_all()
