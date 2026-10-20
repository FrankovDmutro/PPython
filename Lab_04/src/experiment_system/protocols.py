from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from experiment_system.models import Experiment, ExperimentSeries


# ABC: Nominal Interface Contract
class AnalysisStrategy(ABC):
    """Abstract strategy for statistical analysis of experimental data."""

    @abstractmethod
    def analyze(self, values: list[float]) -> dict[str, float]:
        """Calculates statistical metrics."""
        ...


class StandardAnalysisStrategy(AnalysisStrategy):
    """Computes average, minimum, and maximum."""

    def analyze(self, values: list[float]) -> dict[str, float]:
        if not values:
            return {"count": 0.0, "average": 0.0, "min": 0.0, "max": 0.0}
        return {
            "count": float(len(values)),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }


# Structural Typing Protocol: Exporter
@runtime_checkable
class ExperimentExporter(Protocol):
    """Protocol for exporting series results without explicit inheritance."""

    def export(self, series: ExperimentSeries) -> str:
        ...


# Structural Typing Protocol: Notifier
class Notifier(Protocol):
    """Protocol for notification dispatching."""

    def notify(self, recipient: str, message: str) -> None:
        ...