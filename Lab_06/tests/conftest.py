"""Shared pytest fixtures and configuration for test suite."""

from pathlib import Path
from typing import Generator
import pytest

from experiment_tracker.models import Experiment, Measurement, Researcher
from experiment_tracker.repository import InMemoryExperimentRepository


@pytest.fixture
def sample_researcher() -> Researcher:
    """Fixture providing a standard test researcher."""
    return Researcher(
        id="RES-001",
        name="Dr. Frankov",
        department="Quantum Dynamics",
    )


@pytest.fixture
def sample_experiment(sample_researcher: Researcher) -> Experiment:
    """Fixture providing an empty test experiment."""
    return Experiment(
        id="EXP-TEST-01",
        title="Cryogenic Thermal Expansion",
        researcher=sample_researcher,
        parameter="temperature",
    )


@pytest.fixture
def populated_experiment(sample_experiment: Experiment) -> Experiment:
    """Fixture providing an experiment populated with multiple measurements."""
    sample_experiment.add_measurement(Measurement(value=20.0, unit="celsius", timestamp="2026-04-10"))
    sample_experiment.add_measurement(Measurement(value=25.5, unit="celsius", timestamp="2026-04-11"))
    sample_experiment.add_measurement(Measurement(value=30.0, unit="celsius", timestamp="2026-04-12"))
    return sample_experiment


@pytest.fixture
def in_memory_repo() -> Generator[InMemoryExperimentRepository, None, None]:
    """Fixture providing isolated in-memory repository with teardown verification."""
    repo = InMemoryExperimentRepository()
    yield repo
    # Teardown logic
    repo._storage.clear()


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Fixture creating an isolated sample CSV file in pytest tmp_path."""
    csv_file = tmp_path / "measurements_fixture.csv"
    csv_file.write_text(
        "experiment_id,title,researcher,department,parameter,unit,value,date\n"
        "EXP-F1,Fixture Exp 1,Dr. Frankov,Quantum,temperature,celsius,21.5,2026-04-01\n"
        "EXP-F2,Fixture Exp 2,Dr. Smith,Optics,pressure,pascal,101300.0,2026-04-02\n",
        encoding="utf-8",
    )
    return csv_file
