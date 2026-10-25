"""Repository protocols and in-memory fake implementation."""

from typing import Protocol

from experiment_tracker.exceptions import EntityNotFoundError, StorageError
from experiment_tracker.models import Experiment


class ExperimentRepository(Protocol):
    """Protocol for experiment storage and retrieval."""

    def save(self, experiment: Experiment) -> None:
        """Persist or update an experiment."""
        ...

    def get(self, experiment_id: str) -> Experiment | None:
        """Retrieve experiment by id or None if missing."""
        ...

    def list_all(self) -> list[Experiment]:
        """List all stored experiments."""
        ...

    def find_by_researcher(self, researcher_name: str) -> list[Experiment]:
        """Find all experiments associated with researcher name."""
        ...

    def delete(self, experiment_id: str) -> bool:
        """Delete experiment by id."""
        ...


class InMemoryExperimentRepository:
    """Fake repository implementation for state testing and fast isolated tests."""

    def __init__(self) -> None:
        self._storage: dict[str, Experiment] = {}
        self.simulate_failure: bool = False

    def save(self, experiment: Experiment) -> None:
        if self.simulate_failure:
            raise StorageError("Simulated storage write failure")
        self._storage[experiment.id] = experiment

    def get(self, experiment_id: str) -> Experiment | None:
        if self.simulate_failure:
            raise StorageError("Simulated storage read failure")
        return self._storage.get(experiment_id)

    def list_all(self) -> list[Experiment]:
        if self.simulate_failure:
            raise StorageError("Simulated storage query failure")
        return list(self._storage.values())

    def find_by_researcher(self, researcher_name: str) -> list[Experiment]:
        if self.simulate_failure:
            raise StorageError("Simulated storage query failure")
        target = researcher_name.strip().lower()
        return [
            exp for exp in self._storage.values()
            if exp.researcher.name.strip().lower() == target
        ]

    def delete(self, experiment_id: str) -> bool:
        if self.simulate_failure:
            raise StorageError("Simulated storage delete failure")
        if experiment_id in self._storage:
            del self._storage[experiment_id]
            return True
        return False
