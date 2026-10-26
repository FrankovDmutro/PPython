"""Domain models for scientific experiments tracking and optimization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True, frozen=True)
class Researcher:
    """Researcher domain model."""

    id: int
    name: str
    department: str


@dataclass(slots=True, frozen=True)
class Experiment:
    """Scientific experiment record model."""

    id: int
    title: str
    researcher_id: int
    parameter: str
    result: float
    date: date
    notes: Optional[str] = None


@dataclass(slots=True)
class ExperimentStatistics:
    """Statistical summary of experiment results."""

    count: int
    mean: float
    min: float
    max: float
    variance: float
    std_dev: float
    calibrated_mean: float
