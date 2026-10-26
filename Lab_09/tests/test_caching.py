"""Tests for caching, telemetry, and cache invalidation."""

from __future__ import annotations

import time
from typing import List

import pytest

from experiment_optimizer.caching import (
    ExperimentStatsCache,
    cached_heavy_computation,
)
from experiment_optimizer.models import Experiment


def test_cache_miss_then_hit(small_experiments: List[Experiment]) -> None:
    """Verify cache miss on first call and hit on subsequent calls."""
    cache = ExperimentStatsCache(maxsize=10)

    # First access -> Miss
    stats1 = cache.get_statistics("batch1", small_experiments)
    assert cache.misses == 1
    assert cache.hits == 0

    # Second access -> Hit
    stats2 = cache.get_statistics("batch1", small_experiments)
    assert cache.hits == 1
    assert cache.misses == 1
    assert stats1.mean == stats2.mean
    assert cache.hit_ratio == 0.5


def test_cache_invalidation(small_experiments: List[Experiment]) -> None:
    """Verify selective and total cache invalidation."""
    cache = ExperimentStatsCache()
    cache.get_statistics("batch1", small_experiments)
    cache.get_statistics("batch2", small_experiments)

    assert cache.total_requests == 2
    assert cache.telemetry_report()["cached_entries"] == 2

    # Invalidate batch1
    invalidated = cache.invalidate("batch1")
    assert invalidated == 1
    assert cache.telemetry_report()["cached_entries"] == 1

    # Total purge
    total_purged = cache.invalidate()
    assert total_purged == 1
    assert cache.telemetry_report()["cached_entries"] == 0


def test_researcher_cache(small_experiments: List[Experiment]) -> None:
    """Test caching of researcher statistics."""
    cache = ExperimentStatsCache()
    r_id = small_experiments[0].researcher_id

    stat1 = cache.get_researcher_statistics("ds1", r_id, small_experiments)
    assert cache.misses == 1

    stat2 = cache.get_researcher_statistics("ds1", r_id, small_experiments)
    assert cache.hits == 1
    assert stat1["mean"] == stat2["mean"]


def test_functools_lru_cache() -> None:
    """Test standard library lru_cache behavior."""
    tup = (10.0, 20.0, 30.0)
    cached_heavy_computation.cache_clear()

    res1 = cached_heavy_computation(tup)
    res2 = cached_heavy_computation(tup)
    assert res1 == res2
    assert cached_heavy_computation.cache_info().hits == 1
