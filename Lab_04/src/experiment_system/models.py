from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from experiment_system.value_objects import MeasurementUnit


# Domain Entity 1: Researcher (Dataclass)
@dataclass(slots=True)
class Researcher:
    name: str
    email: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Researcher name cannot be empty.")
        if "@" not in self.email:
            raise ValueError("Invalid email address format.")

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


# Domain Entity 2: Measurement (Dataclass Value Representation)
@dataclass(slots=True)
class Measurement:
    parameter: str
    value: float
    unit: MeasurementUnit

    def __post_init__(self) -> None:
        if not self.parameter.strip():
            raise ValueError("Parameter name cannot be empty.")

    def __str__(self) -> str:
        return f"{self.parameter}: {self.value:.4f} {self.unit}"


# Domain Entity 3: ExperimentResult (Base Class demonstrating Inheritance)
class ExperimentResult:
    """Base domain class for experiment evaluation."""

    def __init__(self, raw_value: float) -> None:
        self._raw_value = raw_value

    @property
    def value(self) -> float:
        return self._raw_value

    def is_valid(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"{self.value:.4f}"


class NumericExperimentResult(ExperimentResult):
    """Specialized experiment result with numerical range boundary validation."""

    def __init__(self, raw_value: float, min_bound: float, max_bound: float) -> None:
        super().__init__(raw_value)
        self.min_bound = min_bound
        self.max_bound = max_bound

    def is_valid(self) -> bool:
        return self.min_bound <= self._raw_value <= self.max_bound


class CalibratedExperimentResult(NumericExperimentResult):
    """Calibrated result adjusted by instrument offset."""

    def __init__(
        self,
        raw_value: float,
        min_bound: float,
        max_bound: float,
        offset: float,
    ) -> None:
        super().__init__(raw_value, min_bound, max_bound)
        self.offset = offset

    @property
    def value(self) -> float:
        return self._raw_value + self.offset


# Domain Entity 4: Experiment (Core Entity with Composition)
class Experiment:
    """Experiment entity holding measurements, researcher, and results."""

    def __init__(
        self,
        experiment_id: int,
        title: str,
        researcher: Researcher,  # Composition: Experiment has-a Researcher
        measurement: Measurement,  # Composition: Experiment has-a Measurement
        result: ExperimentResult,
    ) -> None:
        if experiment_id <= 0:
            raise ValueError("Experiment ID must be a positive integer.")
        self.id = experiment_id
        self._title = title.strip()
        self.researcher = researcher
        self.measurement = measurement
        self.result = result
        self.created_at = datetime.now()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Title cannot be empty.")
        self._title = value.strip()

    def __repr__(self) -> str:
        return (
            f"Experiment(id={self.id}, title={self.title!r}, "
            f"researcher={self.researcher!r}, result={self.result!r})"
        )

    def __str__(self) -> str:
        return f"Exp #{self.id} '{self.title}' by {self.researcher.name} -> {self.result}"


# Domain Entity 5: ExperimentSeries (Container Class with Dunder Methods)
@dataclass
class ExperimentSeries:
    """Collection of experiments implementing container dunder methods."""

    series_name: str
    experiments: list[Experiment] = field(default_factory=list)

    def add(self, experiment: Experiment) -> None:
        self.experiments.append(experiment)

    def __len__(self) -> int:
        return len(self.experiments)

    def __iter__(self) -> Iterator[Experiment]:
        return iter(self.experiments)

    def __contains__(self, experiment_id: object) -> bool:
        if not isinstance(experiment_id, int):
            return False
        return any(exp.id == experiment_id for exp in self.experiments)

    def get_values(self) -> list[float]:
        return [exp.result.value for exp in self.experiments]