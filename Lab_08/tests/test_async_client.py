"""Tests for the asynchronous HTTP client, semaphore concurrency, timeout, and retry logic."""

import asyncio
from typing import Dict, List
import httpx
import pytest
from httpx import ASGITransport, AsyncClient, Response

from experiment_manager.api import app
from experiment_manager.async_client import (
    AsyncExperimentClient,
    fetch_multiple_researchers_concurrently,
    fetch_with_retry,
)


@pytest.mark.asyncio
async def test_fetch_with_retry_success():
    """Test fetch_with_retry succeeds when endpoint responds with 200."""
    call_count = 0

    def handler(request: httpx.Request) -> Response:
        nonlocal call_count
        call_count += 1
        return Response(200, json={"status": "ok", "value": 42})

    transport = httpx.MockTransport(handler)
    async with AsyncClient(transport=transport) as client:
        result = await fetch_with_retry(client, "http://mock/test", retries=3)
        assert result == {"status": "ok", "value": 42}
        assert call_count == 1


@pytest.mark.asyncio
async def test_fetch_with_retry_transient_failures_then_success():
    """Test retry triggers upon 503 Server Error and succeeds on 3rd attempt."""
    call_count = 0

    def handler(request: httpx.Request) -> Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return Response(503, json={"error": "Service Unavailable"})
        return Response(200, json={"status": "recovered"})

    transport = httpx.MockTransport(handler)
    async with AsyncClient(transport=transport) as client:
        result = await fetch_with_retry(
            client, "http://mock/test", retries=3, backoff_factor=0.01
        )
        assert result == {"status": "recovered"}
        assert call_count == 3


@pytest.mark.asyncio
async def test_fetch_with_retry_exhausted_raises():
    """Test retry raises exception when all attempts fail."""
    def handler(request: httpx.Request) -> Response:
        return Response(500, json={"error": "Permanent Failure"})

    transport = httpx.MockTransport(handler)
    async with AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_with_retry(
                client, "http://mock/test", retries=2, backoff_factor=0.01
            )


@pytest.mark.asyncio
async def test_async_client_concurrency_and_semaphore(async_client: AsyncClient):
    """Test concurrent gathering across researchers using AsyncExperimentClient and ASGITransport."""
    # Seed researchers with experiments
    r1 = (await async_client.post("/researchers", json={"name": "Scientist A", "department": "Biology"})).json()
    r2 = (await async_client.post("/researchers", json={"name": "Scientist B", "department": "Chemistry"})).json()

    await async_client.post("/experiments", json={"title": "Bio Test", "parameter": "Cell Growth", "result": 150.0, "date": "2026-04-01", "researcher_id": r1["id"]})
    await async_client.post("/experiments", json={"title": "Chem Test", "parameter": "Reaction Rate", "result": 85.0, "date": "2026-04-02", "researcher_id": r2["id"]})

    # Test concurrent aggregation using the active test client
    batch_response = await fetch_multiple_researchers_concurrently(
        researcher_ids=[r1["id"], r2["id"]],
        base_url="http://test",
        max_concurrency=2,
        timeout=5.0,
        retries=2,
        client=async_client,
    )

    assert batch_response.total_queries == 2
    assert batch_response.successful_queries == 2
    assert batch_response.failed_queries == 0
    assert len(batch_response.results) == 2

    # Test high-level AsyncExperimentClient manager
    async with AsyncExperimentClient(base_url="http://test", client=async_client) as client_mgr:
        res = await client_mgr.aggregate_statistics_concurrently(
            researcher_ids=[r1["id"], r2["id"]],
            max_concurrency=1,
            timeout=5.0,
        )
        assert res.successful_queries == 2


@pytest.mark.asyncio
async def test_async_client_get_single_researcher_and_internal_client():
    """Test get_researcher_statistics and default client instantiation in AsyncExperimentClient."""
    def handler(request: httpx.Request) -> Response:
        return Response(200, json={"researcher_id": 5, "researcher_name": "Dr. House", "count": 1, "average": 37.0, "min": 37.0, "max": 37.0})

    transport = httpx.MockTransport(handler)
    async with AsyncClient(transport=transport, base_url="http://mock") as client:
        async with AsyncExperimentClient(base_url="http://mock", client=client) as mgr:
            res = await mgr.get_researcher_statistics(researcher_id=5)
            assert res["researcher_id"] == 5
            assert res["researcher_name"] == "Dr. House"


@pytest.mark.asyncio
async def test_async_client_timeout():
    """Test timeout handling when request exceeds allowed threshold."""
    async def slow_handler(request: httpx.Request) -> Response:
        await asyncio.sleep(0.2)
        return Response(200, json={"ok": True})

    transport = httpx.MockTransport(slow_handler)
    async with AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.TimeoutException):
            await fetch_with_retry(
                client, "http://mock/slow", retries=1, timeout=0.05
            )
