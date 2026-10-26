"""Tests for cProfile, tracemalloc, and execution measurement utilities."""

from __future__ import annotations

import math

from experiment_optimizer.profiling import (
    measure_execution_time,
    profile_with_cprofile,
    profile_with_tracemalloc,
)


def sample_workload(n: int = 10_000) -> float:
    """Sample mathematical workload."""
    return sum(math.sqrt(i) for i in range(n))


def test_measure_execution_time() -> None:
    """Verify execution time measurement returns expected number of samples."""
    durations = measure_execution_time(sample_workload, 1_000, repeats=4)
    assert len(durations) == 4
    assert all(d > 0.0 for d in durations)


def test_profile_with_cprofile() -> None:
    """Verify cProfile returns structured stats and text summary."""
    res, structured, summary = profile_with_cprofile(sample_workload, 5_000, top_n=5)
    assert res > 0
    assert len(structured) > 0
    assert "tottime" in structured[0]
    assert "cumtime" in structured[0]
    assert "ncalls" in structured[0]
    assert len(summary) > 0


def test_profile_with_tracemalloc() -> None:
    """Verify tracemalloc captures memory metrics and top traces."""
    res, cur_kb, peak_kb, traces = profile_with_tracemalloc(sample_workload, 5_000)
    assert res > 0
    assert peak_kb >= 0.0
    assert isinstance(traces, list)
