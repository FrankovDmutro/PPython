"""Pytest fixtures for Lab 09 tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

from experiment_optimizer.dataset import generate_experiments, generate_researchers
from experiment_optimizer.models import Experiment, Researcher


@pytest.fixture
def sample_researchers() -> List[Researcher]:
    """Fixture providing sample researchers."""
    return generate_researchers()


@pytest.fixture
def small_experiments(sample_researchers: List[Researcher]) -> List[Experiment]:
    """Fixture providing 100 deterministic experiments."""
    return generate_experiments(100, researchers=sample_researchers, seed=42)


@pytest.fixture
def medium_experiments(sample_researchers: List[Researcher]) -> List[Experiment]:
    """Fixture providing 1,000 deterministic experiments."""
    return generate_experiments(1_000, researchers=sample_researchers, seed=42)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Fixture providing a temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
