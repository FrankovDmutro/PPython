"""Asynchronous measurement source and client for external sensor hardware."""

import asyncio
from datetime import datetime
import random
from typing import Protocol

from experiment_tracker.exceptions import SensorCommunicationError
from experiment_tracker.models import Measurement


class AsyncMeasurementSource(Protocol):
    """Protocol for asynchronous telemetry/sensor data sources."""

    async def fetch_measurement(self, sensor_id: str) -> Measurement:
        """Asynchronously read latest measurement from external sensor."""
        ...


class AsyncSensorClient:
    """Production asynchronous client simulating hardware sensor communications."""

    def __init__(self, endpoint_url: str = "https://sensors.lab.internal/api/v1") -> None:
        self.endpoint_url = endpoint_url
        self.is_connected = False

    async def connect(self) -> None:
        """Establish async connection."""
        await asyncio.sleep(0.01)
        self.is_connected = True

    async def disconnect(self) -> None:
        """Close connection."""
        await asyncio.sleep(0.01)
        self.is_connected = False

    async def fetch_measurement(self, sensor_id: str) -> Measurement:
        """Fetch telemetry with simulated network latency and timeout check."""
        if not sensor_id.strip():
            raise SensorCommunicationError("Sensor identifier cannot be empty")

        await asyncio.sleep(0.02)
        # Deterministic simulation based on sensor_id
        timestamp = datetime.now().isoformat()
        if "temp" in sensor_id.lower():
            return Measurement(value=25.4, unit="celsius", timestamp=timestamp)
        elif "press" in sensor_id.lower():
            return Measurement(value=101325.0, unit="pascal", timestamp=timestamp)
        else:
            return Measurement(value=5.0, unit="volt", timestamp=timestamp)

    async def ingest_stream(self, sensor_id: str, count: int) -> list[Measurement]:
        """Ingest multiple measurements asynchronously."""
        results: list[Measurement] = []
        for _ in range(count):
            meas = await self.fetch_measurement(sensor_id)
            results.append(meas)
            await asyncio.sleep(0.01)
        return results
