"""Service layer orchestrating experiment domain logic, analysis, and exports."""

from pathlib import Path
from typing import Any, Protocol

from experiment_tracker.async_sensor import AsyncMeasurementSource
from experiment_tracker.exceptions import (
    EntityNotFoundError,
    ExportError,
    StorageError,
    ValidationError,
)
from experiment_tracker.io import export_experiment_json
from experiment_tracker.models import Experiment, Measurement, Researcher
from experiment_tracker.repository import ExperimentRepository
from experiment_tracker.validators import (
    validate_iso_date,
    validate_measurement_value,
    validate_parameter,
    validate_unit,
)


class AnalysisStrategy(Protocol):
    """Protocol for experiment data analysis algorithms."""

    def compute_summary(self, experiment: Experiment) -> dict[str, Any]:
        """Compute statistical summary report for the experiment."""
        ...


class StatisticalAnalysisStrategy:
    """Standard statistical metrics calculation."""

    def compute_summary(self, experiment: Experiment) -> dict[str, Any]:
        if not experiment.measurements:
            return {
                "experiment_id": experiment.id,
                "measurements_count": 0,
                "average": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std_dev": 0.0,
            }
        return {
            "experiment_id": experiment.id,
            "parameter": experiment.parameter,
            "measurements_count": len(experiment.measurements),
            "average": experiment.average_value(),
            "min": experiment.min_value(),
            "max": experiment.max_value(),
            "std_dev": experiment.std_dev(),
        }


class Exporter(Protocol):
    """Protocol for experiment exporters."""

    def export(self, experiment: Experiment, path: Path) -> Path:
        """Export experiment to destination path."""
        ...


class JsonExperimentExporter:
    """Concrete JSON exporter implementing Exporter protocol."""

    def export(self, experiment: Experiment, path: Path) -> Path:
        return export_experiment_json(experiment, path)


class ExperimentService:
    """Application service coordinating experiment repository, analysis, and external dependencies."""

    def __init__(
        self,
        repository: ExperimentRepository,
        analysis_strategy: AnalysisStrategy | None = None,
        exporter: Exporter | None = None,
    ) -> None:
        self.repository = repository
        self.analysis_strategy = analysis_strategy or StatisticalAnalysisStrategy()
        self.exporter = exporter or JsonExperimentExporter()

    def create_experiment(
        self,
        experiment_id: str,
        title: str,
        researcher: Researcher,
        parameter: str,
    ) -> Experiment:
        """Create, validate, and persist a new experiment."""
        valid_param = validate_parameter(parameter)
        if not title.strip():
            raise ValidationError("Experiment title cannot be empty", field="title")

        experiment = Experiment(
            id=experiment_id.strip(),
            title=title.strip(),
            researcher=researcher,
            parameter=valid_param,
        )
        self.repository.save(experiment)
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment:
        """Fetch experiment by id or raise EntityNotFoundError."""
        exp = self.repository.get(experiment_id)
        if exp is None:
            raise EntityNotFoundError(f"Experiment '{experiment_id}' does not exist")
        return exp

    def record_measurement(
        self,
        experiment_id: str,
        value: float,
        unit: str,
        timestamp: str,
    ) -> Measurement:
        """Validate and append a new measurement to existing experiment."""
        exp = self.get_experiment(experiment_id)
        valid_unit = validate_unit(unit)
        valid_val = validate_measurement_value(value, exp.parameter)
        valid_date = validate_iso_date(timestamp)

        measurement = Measurement(value=valid_val, unit=valid_unit, timestamp=valid_date)
        exp.add_measurement(measurement)
        self.repository.save(exp)
        return measurement

    def analyze_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Perform statistical analysis on experiment measurements."""
        exp = self.get_experiment(experiment_id)
        return self.analysis_strategy.compute_summary(exp)

    def export_experiment(self, experiment_id: str, destination: Path) -> Path:
        """Export experiment using configured exporter."""
        exp = self.get_experiment(experiment_id)
        return self.exporter.export(exp, destination)

    def search_by_researcher(self, researcher_name: str) -> list[Experiment]:
        """Search experiments conducted by researcher."""
        return self.repository.find_by_researcher(researcher_name)

    async def ingest_from_sensor(
        self,
        experiment_id: str,
        sensor: AsyncMeasurementSource,
        sensor_id: str,
    ) -> Measurement:
        """Asynchronously read sensor telemetry and attach to experiment."""
        exp = self.get_experiment(experiment_id)
        measurement = await sensor.fetch_measurement(sensor_id)
        valid_val = validate_measurement_value(measurement.value, exp.parameter)
        valid_meas = Measurement(value=valid_val, unit=measurement.unit, timestamp=measurement.timestamp)
        exp.add_measurement(valid_meas)
        self.repository.save(exp)
        return valid_meas
