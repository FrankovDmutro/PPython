"""Unit tests for domain models, aggregates, and value objects."""

import pytest

from experiment_tracker.exceptions import EmptySeriesError
from experiment_tracker.models import Experiment, ExperimentSeries, Measurement, Researcher


@pytest.mark.unit
def test_researcher_creation(sample_researcher: Researcher) -> None:
    """Test researcher value object attributes and dictionary serialization."""
    # Arrange & Act
    as_dict = sample_researcher.to_dict()

    # Assert
    assert sample_researcher.id == "RES-001"
    assert sample_researcher.name == "Dr. Frankov"
    assert as_dict["department"] == "Quantum Dynamics"


@pytest.mark.unit
def test_measurement_creation() -> None:
    """Test measurement value object."""
    meas = Measurement(value=101.325, unit="pascal", timestamp="2026-04-15")
    assert meas.value == pytest.approx(101.325)
    assert meas.unit == "pascal"
    assert meas.to_dict()["timestamp"] == "2026-04-15"


@pytest.mark.unit
def test_experiment_add_measurement(sample_experiment: Experiment) -> None:
    """Test adding measurements to experiment entity."""
    meas = Measurement(value=22.4, unit="celsius", timestamp="2026-04-15")
    sample_experiment.add_measurement(meas)

    assert len(sample_experiment.measurements) == 1
    assert sample_experiment.measurements[0] == meas


@pytest.mark.unit
def test_experiment_statistics(populated_experiment: Experiment) -> None:
    """Test average, min, max, and std_dev calculation using pytest.approx."""
    # Populated with [20.0, 25.5, 30.0]
    expected_avg = (20.0 + 25.5 + 30.0) / 3

    assert populated_experiment.average_value() == pytest.approx(expected_avg, rel=1e-3)
    assert populated_experiment.min_value() == pytest.approx(20.0)
    assert populated_experiment.max_value() == pytest.approx(30.0)
    assert populated_experiment.std_dev() > 0.0


@pytest.mark.unit
def test_empty_experiment_raises_custom_exception(sample_experiment: Experiment) -> None:
    """Test that computing statistics on empty experiment raises EmptySeriesError."""
    with pytest.raises(EmptySeriesError) as exc_info:
        sample_experiment.average_value()

    assert "Cannot compute average for empty experiment" in str(exc_info.value)
    assert sample_experiment.id in str(exc_info.value)

    with pytest.raises(EmptySeriesError):
        sample_experiment.min_value()

    with pytest.raises(EmptySeriesError):
        sample_experiment.max_value()


@pytest.mark.unit
def test_filter_by_range(populated_experiment: Experiment) -> None:
    """Test filtering measurements by numerical interval."""
    # Values: [20.0, 25.5, 30.0]
    filtered = populated_experiment.filter_by_range(22.0, 28.0)
    assert len(filtered) == 1
    assert filtered[0].value == pytest.approx(25.5)

    empty_filter = populated_experiment.filter_by_range(50.0, 100.0)
    assert len(empty_filter) == 0


@pytest.mark.unit
def test_experiment_series_aggregation(sample_researcher: Researcher) -> None:
    """Test ExperimentSeries grouping and overall average calculation."""
    series = ExperimentSeries(series_id="SER-01", parameter="temperature")

    exp1 = Experiment("E1", "Exp 1", sample_researcher, "temperature")
    exp1.add_measurement(Measurement(10.0, "celsius", "2026-04-01"))
    exp2 = Experiment("E2", "Exp 2", sample_researcher, "temperature")
    exp2.add_measurement(Measurement(30.0, "celsius", "2026-04-02"))

    series.add_experiment(exp1)
    series.add_experiment(exp2)

    assert series.total_measurements() == 2
    assert series.overall_average() == pytest.approx(20.0)


@pytest.mark.unit
def test_experiment_series_mismatched_parameter(sample_researcher: Researcher) -> None:
    """Test error when adding mismatched parameter experiment to series."""
    series = ExperimentSeries(series_id="SER-02", parameter="temperature")
    mismatched = Experiment("E-ERR", "Pressure Test", sample_researcher, "pressure")

    with pytest.raises(ValueError) as exc_info:
        series.add_experiment(mismatched)

    assert "Cannot add experiment with parameter 'pressure'" in str(exc_info.value)
