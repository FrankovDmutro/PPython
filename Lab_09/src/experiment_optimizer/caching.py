"""Caching system with telemetry, hit/miss tracking, and cache invalidation."""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from .analytics import calculate_statistics_sequential, group_by_researcher_sequential
from .models import Experiment, ExperimentStatistics


class ExperimentStatsCache:
    """In-memory cache for experiment analytics with telemetry and invalidation support."""

    def __init__(self, maxsize: int = 128) -> None:
        self.maxsize = maxsize
        self._cache: Dict[str, Any] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._total_time_saved_sec: float = 0.0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def total_requests(self) -> int:
        return self._hits + self._misses

    @property
    def hit_ratio(self) -> float:
        total = self.total_requests
        return (self._hits / total) if total > 0 else 0.0

    @property
    def time_saved(self) -> float:
        return self._total_time_saved_sec

    def get_statistics(
        self,
        dataset_key: str,
        experiments: Sequence[Experiment],
        compute_fn: Callable[[Sequence[Experiment]], ExperimentStatistics] = calculate_statistics_sequential,
    ) -> ExperimentStatistics:
        """Retrieve overall dataset statistics from cache or compute and cache it."""
        cache_key = f"stats::{dataset_key}"

        if cache_key in self._cache:
            self._hits += 1
            entry = self._cache[cache_key]
            self._total_time_saved_sec += entry["compute_duration"]
            return entry["data"]

        # Cache miss
        self._misses += 1
        t0 = time.perf_counter()
        stats = compute_fn(experiments)
        duration = time.perf_counter() - t0

        if len(self._cache) >= self.maxsize:
            # Evict first inserted key (FIFO)
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self._cache[cache_key] = {
            "data": stats,
            "compute_duration": duration,
        }
        return stats

    def get_researcher_statistics(
        self,
        dataset_key: str,
        researcher_id: int,
        experiments: Sequence[Experiment],
    ) -> Dict[str, float]:
        """Retrieve aggregated statistics for a specific researcher."""
        cache_key = f"researcher::{dataset_key}::{researcher_id}"

        if cache_key in self._cache:
            self._hits += 1
            entry = self._cache[cache_key]
            self._total_time_saved_sec += entry["compute_duration"]
            return entry["data"]

        self._misses += 1
        t0 = time.perf_counter()
        grouped = group_by_researcher_sequential(experiments)
        researcher_stat = grouped.get(
            researcher_id, {"count": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
        )
        duration = time.perf_counter() - t0

        if len(self._cache) >= self.maxsize:
            first_key = next(iter(self._cache))
            del self._cache[first_key]

        self._cache[cache_key] = {
            "data": researcher_stat,
            "compute_duration": duration,
        }
        return researcher_stat

    def invalidate(self, dataset_key: Optional[str] = None) -> int:
        """Invalidate cached entries for a dataset or purge entire cache.

        Returns number of invalidated keys.
        """
        if dataset_key is None:
            count = len(self._cache)
            self._cache.clear()
            return count

        prefix = f"::{dataset_key}"
        keys_to_del = [k for k in self._cache if prefix in k or k == f"stats::{dataset_key}"]
        for k in keys_to_del:
            del self._cache[k]
        return len(keys_to_del)

    def telemetry_report(self) -> Dict[str, Any]:
        """Return cache performance telemetry."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": self.total_requests,
            "hit_ratio_percent": round(self.hit_ratio * 100, 2),
            "time_saved_seconds": round(self._total_time_saved_sec, 6),
            "cached_entries": len(self._cache),
        }


# Standard library lru_cache function for comparison
@lru_cache(maxsize=128)
def cached_heavy_computation(param_tuple: Tuple[float, ...]) -> float:
    """Demonstration of functools.lru_cache for pure numerical tuples."""
    total = 0.0
    for x in param_tuple:
        total += 1.05 * x - 0.0002 * (x**2)
    return total / len(param_tuple) if param_tuple else 0.0
