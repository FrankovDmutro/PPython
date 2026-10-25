"""Tests for asynchronous sensor telemetry and AsyncMock integration."""

from unittest.mock import AsyncMock
import pytest

from experiment_tracker.async_sensor import AsyncMeasurementSource, AsyncSensorClient
from experiment_tracker.exceptions import SensorCommunicationError
from experiment_tracker.models import Experiment, Measurement
from experiment_tracker.repository import InMemoryExperimentRepository
from experiment_tracker.services import ExperimentService


@pytest.mark.async_test
@pytest.mark.unit
async def test_async_sensor_client_direct_call() -> None:
    """Test concrete AsyncSensorClient read."""
    client = AsyncSensorClient()
    meas = await client.fetch_measurement("sensor-temp-01")

    assert meas.unit == "celsius"
    assert meas.value == pytest.approx(25.4)


@pytest.mark.async_test
@pytest.mark.unit
async def test_async_sensor_client_empty_sensor_id_raises() -> None:
    """Test sensor client error handling for empty sensor id."""
    client = AsyncSensorClient()
    with pytest.raises(SensorCommunicationError):
        await client.fetch_measurement("   ")


@pytest.mark.async_test
@pytest.mark.unit
async def test_service_ingest_from_sensor_using_async_mock(sample_experiment: Experiment) -> None:
    """Test asynchronous sensor ingestion using AsyncMock with awaited assertion."""
    # Arrange
    repo = InMemoryExperimentRepository()
    repo.save(sample_experiment)
    service = ExperimentService(repo)

    mock_sensor = AsyncMock(spec=AsyncMeasurementSource)
    mock_sensor.fetch_measurement.return_value = Measurement(
        value=28.75,
        unit="celsius",
        timestamp="2026-04-18T10:00:00",
    )

    # Act
    meas = await service.ingest_from_sensor(
        experiment_id=sample_experiment.id,
        sensor=mock_sensor,
        sensor_id="TEMP-EXTERNAL-99",
    )

    # Assert
    assert meas.value == pytest.approx(28.75)
    # Verify awaited call on mock
    mock_sensor.fetch_measurement.assert_awaited_once_with("TEMP-EXTERNAL-99")

    # Verify state updated in experiment
    updated = repo.get(sample_experiment.id)
    assert updated is not None
    assert len(updated.measurements) == 1
    assert updated.measurements[0].value == pytest.approx(28.75)


@pytest.mark.async_test
@pytest.mark.unit
async def test_async_sensor_failure_path_side_effect(sample_experiment: Experiment) -> None:
    """Test handling of async sensor failure via side_effect."""
    repo = InMemoryExperimentRepository()
    repo.save(sample_experiment)
    service = ExperimentService(repo)

    mock_sensor = AsyncMock(spec=AsyncMeasurementSource)
    mock_sensor.fetch_measurement.side_effect = SensorCommunicationError("Network timeout connecting to sensor")

    with pytest.raises(SensorCommunicationError) as exc_info:
        await service.ingest_from_sensor(sample_experiment.id, mock_sensor, "FAIL-SENSOR")

    assert "Network timeout" in str(exc_info.value)
