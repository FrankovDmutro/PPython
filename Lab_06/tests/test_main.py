"""Tests for main CLI entrypoint and additional async sensor operations."""

from pathlib import Path
import pytest

from experiment_tracker.async_sensor import AsyncSensorClient
from experiment_tracker.main import main


@pytest.mark.unit
def test_main_cli_success(sample_csv_file: Path, tmp_path: Path) -> None:
    """Test CLI main function executes end to end."""
    out_file = tmp_path / "main_output.json"
    exit_code = main(["--input", str(sample_csv_file), "--output", str(out_file)])
    assert exit_code == 0
    assert out_file.is_file()


@pytest.mark.unit
def test_main_cli_missing_input(tmp_path: Path) -> None:
    """Test CLI returns exit code 1 when input CSV does not exist."""
    missing = tmp_path / "non_existent.csv"
    exit_code = main(["--input", str(missing)])
    assert exit_code == 1


@pytest.mark.async_test
@pytest.mark.unit
async def test_async_sensor_client_lifecycle_and_streaming() -> None:
    """Test connect, disconnect, and streaming ingestion."""
    client = AsyncSensorClient()
    assert client.is_connected is False

    await client.connect()
    assert client.is_connected is True

    # Test pressure and default sensor branches
    meas_press = await client.fetch_measurement("sensor-press-99")
    assert meas_press.unit == "pascal"

    meas_volt = await client.fetch_measurement("sensor-volt-05")
    assert meas_volt.unit == "volt"

    # Test stream ingestion
    stream = await client.ingest_stream("sensor-temp-01", count=2)
    assert len(stream) == 2

    await client.disconnect()
    assert client.is_connected is False
