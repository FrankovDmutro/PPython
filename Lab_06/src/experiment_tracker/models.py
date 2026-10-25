"""Domain models for scientific experiments, measurements, and researchers."""

from dataclasses import asdict, dataclass, field
import statistics
from typing import Any

from experiment_tracker.exceptions import EmptySeriesError


@dataclass(frozen=True, slots=True)
class Researcher:
    """Researcher value object."""

    id: str
    name: str
    department: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Measurement:
    """Single scientific measurement with unit and timestamp."""

    value: float
    unit: str
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Experiment:
    """Experiment entity containing metadata and series of measurements."""

    id: str
    title: str
    researcher: Researcher
    parameter: str
    measurements: list[Measurement] = field(default_factory=list)

    def add_measurement(self, measurement: Measurement) -> None:
        """Add a new measurement to the experiment series."""
        self.measurements.append(measurement)

    def average_value(self) -> float:
        """Compute arithmetic mean of measurement values."""
        if not self.measurements:
            raise EmptySeriesError(f"Cannot compute average for empty experiment '{self.id}'")
        return sum(m.value for m in self.measurements) / len(self.measurements)

    def min_value(self) -> float:
        """Find minimum measurement value."""
        if not self.measurements:
            raise EmptySeriesError(f"Cannot determine min value for empty experiment '{self.id}'")
        return min(m.value for m in self.measurements)

    def max_value(self) -> float:
        """Find maximum measurement value."""
        if not self.measurements:
            raise EmptySeriesError(f"Cannot determine max value for empty experiment '{self.id}'")
        return max(m.value for m in self.measurements)

    def std_dev(self) -> float:
        """Calculate standard deviation of measurement values."""
        if len(self.measurements) < 2:
            return 0.0
        return statistics.stdev(m.value for m in self.measurements)

    def filter_by_range(self, min_val: float, max_val: float) -> list[Measurement]:
        """Filter measurements within [min_val, max_val] interval."""
        return [m for m in self.measurements if min_val <= m.value <= max_val]

    def to_dict(self) -> dict[str, Any]:
        """Convert experiment to JSON-serializable dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "researcher": self.researcher.to_dict(),
            "parameter": self.parameter,
            "measurements_count": len(self.measurements),
            "measurements": [m.to_dict() for m in self.measurements],
        }


@dataclass
class ExperimentSeries:
    """Aggregate grouping multiple experiments of a specific parameter."""

    series_id: str
    parameter: str
    experiments: list[Experiment] = field(default_factory=list)

    def add_experiment(self, experiment: Experiment) -> None:
        if experiment.parameter.lower() != self.parameter.lower():
            raise ValueError(
                f"Cannot add experiment with parameter '{experiment.parameter}' to series of '{self.parameter}'"
            )
        self.experiments.append(experiment)

    def total_measurements(self) -> int:
        return sum(len(e.measurements) for e in self.experiments)

    def overall_average(self) -> float:
        all_vals = [m.value for e in self.experiments for m in e.measurements]
        if not all_vals:
            raise EmptySeriesError(f"Series '{self.series_id}' contains no measurements")
        return sum(all_vals) / len(all_vals)
