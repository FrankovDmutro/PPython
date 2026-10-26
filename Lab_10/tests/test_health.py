"""Tests for the /health operational endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_ok(client: AsyncClient) -> None:
    """Verify that /health returns 200 OK and expected structure."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["database"] == "connected"
    assert "environment" in data
    assert "app_name" in data
