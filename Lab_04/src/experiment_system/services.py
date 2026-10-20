from experiment_system.dto import ExperimentPayload
from experiment_system.models import (
    CalibratedExperimentResult,
    Experiment,
    ExperimentResult,
    ExperimentSeries,
    Measurement,
    NumericExperimentResult,
    Researcher,
)
from experiment_system.protocols import (
    AnalysisStrategy,
    ExperimentExporter,
    Notifier,
)
from experiment_system.repositories import InMemoryRepository
from experiment_system.value_objects import MeasurementUnit


# Structural implementation of Notifier (without explicit inheritance)
class ConsoleNotifier:
    def notify(self, recipient: str, message: str) -> None:
        print(f"[NOTIFICATION to {recipient}]: {message}")


# Structural implementation of ExperimentExporter
class JsonLikeExporter:
    def export(self, series: ExperimentSeries) -> str:
        return (
            f'{{"series": "{series.series_name}", '
            f'"experiments_count": {len(series)}, '
            f'"valid_samples": {len([e for e in series if e.result.is_valid()])}}}'
        )


def experiment_from_payload(payload: ExperimentPayload) -> Experiment:
    """Converts TypedDict payload to fully formed Domain Entity."""
    researcher = Researcher(
        name=payload["researcher_name"],
        email=payload["researcher_email"],
    )
    unit = MeasurementUnit(symbol=payload["unit"], dimension="Physical")
    measurement = Measurement(
        parameter=payload["parameter"],
        value=payload["value"],
        unit=unit,
    )

    result: ExperimentResult
    if "calibration_offset" in payload:
        result = CalibratedExperimentResult(
            raw_value=payload["value"],
            min_bound=0.0,
            max_bound=1000.0,
            offset=payload["calibration_offset"],
        )
    else:
        result = NumericExperimentResult(
            raw_value=payload["value"],
            min_bound=0.0,
            max_bound=1000.0,
        )

    return Experiment(
        experiment_id=payload["id"],
        title=payload["title"],
        researcher=researcher,
        measurement=measurement,
        result=result,
    )


class ExperimentService:
    """Application service coordinating experiments lifecycle via Dependency Injection."""

    def __init__(
        self,
        repository: InMemoryRepository[Experiment],
        analysis_strategy: AnalysisStrategy,
        exporter: ExperimentExporter,
        notifier: Notifier,
    ) -> None:
        self._repo = repository
        self._strategy = analysis_strategy
        self._exporter = exporter
        self._notifier = notifier

    def register_experiment(self, payload: ExperimentPayload) -> Experiment:
        experiment = experiment_from_payload(payload)
        self._repo.add(experiment)

        if not experiment.result.is_valid():
            self._notifier.notify(
                experiment.researcher.email,
                f"Experiment #{experiment.id} exceeds boundary tolerance!",
            )
        return experiment

    def analyze_series(self, series: ExperimentSeries) -> dict[str, float]:
        values = series.get_values()
        return self._strategy.analyze(values)

    def export_series(self, series: ExperimentSeries) -> str:
        return self._exporter.export(series)