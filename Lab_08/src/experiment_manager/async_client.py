"""Asynchronous HTTP client for concurrent experiment statistics aggregation.

Implements asyncio.Task, asyncio.gather, asyncio.Semaphore, timeout handling,
and retry logic with exponential backoff.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from experiment_manager.schemas import (
    BatchStatisticsResponse,
    ResearcherStatisticsResponse,
)

logger = logging.getLogger(__name__)


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    retries: int = 3,
    backoff_factor: float = 0.2,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Fetch URL with timeout and exponential backoff retry on transient errors."""
    last_exception: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            try:
                response = await asyncio.wait_for(
                    client.get(url, timeout=timeout), timeout=timeout
                )
            except asyncio.TimeoutError as te:
                raise httpx.ReadTimeout(f"Request to {url} timed out after {timeout}s") from te

            # If server error (5xx), raise to trigger retry
            if response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            last_exception = exc
            if attempt == retries:
                logger.warning(
                    "Request to %s failed after %d attempts: %s", url, retries, exc
                )
                break
            sleep_time = backoff_factor * (2 ** (attempt - 1))
            logger.info(
                "Attempt %d/%d failed for %s. Retrying in %.2fs...",
                attempt,
                retries,
                url,
                sleep_time,
            )
            await asyncio.sleep(sleep_time)

    if last_exception:
        raise last_exception
    raise RuntimeError(f"Unknown error fetching {url}")


async def fetch_researcher_statistics_limited(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    researcher_id: int,
    base_url: str = "http://127.0.0.1:8000",
    retries: int = 3,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """Fetch statistics for a single researcher bounded by an asyncio.Semaphore."""
    async with semaphore:
        url = f"{base_url.rstrip('/')}/researchers/{researcher_id}/statistics"
        return await fetch_with_retry(client, url, retries=retries, timeout=timeout)


async def fetch_multiple_researchers_concurrently(
    researcher_ids: List[int],
    base_url: str = "http://127.0.0.1:8000",
    max_concurrency: int = 3,
    timeout: float = 5.0,
    retries: int = 2,
    client: Optional[httpx.AsyncClient] = None,
) -> BatchStatisticsResponse:
    """Fetch statistics for multiple researchers concurrently using Task, gather, Semaphore, and retry."""
    start_time = time.perf_counter()
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_fetch(active_client: httpx.AsyncClient) -> BatchStatisticsResponse:
        # Create explicit asyncio.Task instances
        tasks: List[asyncio.Task] = [
            asyncio.create_task(
                fetch_researcher_statistics_limited(
                    semaphore=semaphore,
                    client=active_client,
                    researcher_id=r_id,
                    base_url=base_url,
                    retries=retries,
                    timeout=timeout,
                )
            )
            for r_id in researcher_ids
        ]

        # Gather results with exception capturing
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_items: List[ResearcherStatisticsResponse] = []
        failed_count = 0

        for res in raw_results:
            if isinstance(res, Exception):
                failed_count += 1
                logger.error("Failed task in batch fetch: %s", res)
            elif isinstance(res, dict):
                try:
                    stat_model = ResearcherStatisticsResponse(**res)
                    successful_items.append(stat_model)
                except Exception as parse_err:
                    failed_count += 1
                    logger.error("Error parsing response: %s", parse_err)
            else:
                failed_count += 1

        duration = round(time.perf_counter() - start_time, 4)
        return BatchStatisticsResponse(
            total_queries=len(researcher_ids),
            successful_queries=len(successful_items),
            failed_queries=failed_count,
            results=successful_items,
            duration_seconds=duration,
        )

    if client is not None:
        return await _run_fetch(client)

    async with httpx.AsyncClient() as new_client:
        return await _run_fetch(new_client)


class AsyncExperimentClient:
    """High-level asynchronous experiment client manager."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._external_client = client
        self._internal_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "AsyncExperimentClient":
        if self._external_client is None:
            self._internal_client = httpx.AsyncClient(base_url=self.base_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._internal_client is not None:
            await self._internal_client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        return self._external_client or self._internal_client  # type: ignore

    async def get_researcher_statistics(
        self, researcher_id: int, timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Fetch statistics for a single researcher."""
        return await fetch_with_retry(
            self.client,
            f"{self.base_url}/researchers/{researcher_id}/statistics",
            timeout=timeout,
        )

    async def aggregate_statistics_concurrently(
        self,
        researcher_ids: List[int],
        max_concurrency: int = 3,
        timeout: float = 5.0,
        retries: int = 2,
    ) -> BatchStatisticsResponse:
        """Run parallel batch statistics collection."""
        return await fetch_multiple_researchers_concurrently(
            researcher_ids=researcher_ids,
            base_url=self.base_url,
            max_concurrency=max_concurrency,
            timeout=timeout,
            retries=retries,
            client=self.client,
        )
