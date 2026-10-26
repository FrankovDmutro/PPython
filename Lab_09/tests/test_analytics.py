"""Tests for baseline sequential and NumPy analytics."""

from __future__ import annotations

import math
from typing import List

import numpy as np
import pytest

from experiment_optimizer.analytics import (
    calculate_statistics_numpy,
    calculate_statistics_sequential,
    calibrate_sensor_value,
    filter_by_range_numpy,
    filter_by_range_sequential,
    group_by_researcher_sequential,
)
from experiment_optimizer.models import Experiment


def test_empty_statistics() -> None:
    """Test statistics on empty input."""
    empty_seq = calculate_statistics_sequential([])
    assert empty_seq.count == 0
    assert empty_seq.mean == 0.0

    empty_np = calculate_statistics_numpy([])
    assert empty_np.count == 0
    assert empty_np.mean == 0.0


def test_calculate_statistics_known_values() -> None:
    """Test statistics computation against manual known values."""
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = calculate_statistics_sequential(values)

    assert stats.count == 5
    assert stats.mean == 30.0
    assert stats.min == 10.0
    assert stats.max == 50.0
    # Variance for [10, 20, 30, 40, 50]: (400 + 100 + 0 + 100 + 400)/5 = 200
    assert math.isclose(stats.variance, 200.0, rel_tol=1e-5)
    assert math.isclose(stats.std_dev, math.sqrt(200.0), rel_tol=1e-5)


def test_baseline_vs_numpy_alignment(small_experiments: List[Experiment]) -> None:
    """Verify that NumPy vectorized analytics produces strictly identical results to sequential baseline."""
    base_stats = calculate_statistics_sequential(small_experiments)
    np_stats = calculate_statistics_numpy(small_experiments)

    assert base_stats.count == np_stats.count
    assert math.isclose(base_stats.mean, np_stats.mean, abs_tol=1e-4)
    assert math.isclose(base_stats.min, np_stats.min, abs_tol=1e-4)
    assert math.isclose(base_stats.max, np_stats.max, abs_tol=1e-4)
    assert math.isclose(base_stats.variance, np_stats.variance, abs_tol=1e-4)
    assert math.isclose(base_stats.std_dev, np_stats.std_dev, abs_tol=1e-4)
    assert math.isclose(base_stats.calibrated_mean, np_stats.calibrated_mean, abs_tol=1e-4)


def test_filter_by_range(small_experiments: List[Experiment]) -> None:
    """Verify filtering behavior on both sequential and NumPy implementations."""
    min_val, max_val = 100.0, 250.0
    filtered_seq = filter_by_range_sequential(small_experiments, min_val, max_val)

    # Check bounds
    for exp in filtered_seq:
        assert min_val <= exp.result <= max_val

    # NumPy check
    arr = np.array([e.result for e in small_experiments], dtype=np.float64)
    filtered_np = filter_by_range_numpy(arr, min_val, max_val)

    assert len(filtered_seq) == len(filtered_np)
    if len(filtered_seq) > 0:
        assert math.isclose(filtered_seq[0].result, filtered_np[0], abs_tol=1e-4)


def test_group_by_researcher(small_experiments: List[Experiment]) -> None:
    """Test grouping by researcher."""
    grouped = group_by_researcher_sequential(small_experiments)
    assert len(grouped) > 0

    total_count = sum(info["count"] for info in grouped.values())
    assert total_count == len(small_experiments)

    for r_id, info in grouped.items():
        assert info["count"] > 0
        assert info["min"] <= info["mean"] <= info["max"]
