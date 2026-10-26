"""Tests for threading, multiprocessing, and synchronization."""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

import pytest

from experiment_optimizer.analytics import calculate_statistics_sequential
from experiment_optimizer.dataset import (
    export_experiment_batches,
    load_experiments_from_file,
)
from experiment_optimizer.models import Experiment
from experiment_optimizer.parallel import (
    SafeMetricAccumulator,
    UnsafeMetricAccumulator,
    calculate_statistics_multiprocess,
    calculate_statistics_threads,
    load_datasets_sequential,
    load_datasets_threadpool,
    run_race_condition_experiment,
)


def test_threads_vs_baseline(small_experiments: List[Experiment]) -> None:
    """Test that ThreadPoolExecutor yields identical results to Baseline."""
    base_stats = calculate_statistics_sequential(small_experiments)
    thread_stats = calculate_statistics_threads(small_experiments, workers=4)

    assert base_stats.count == thread_stats.count
    assert math.isclose(base_stats.mean, thread_stats.mean, abs_tol=1e-4)
    assert math.isclose(base_stats.min, thread_stats.min, abs_tol=1e-4)
    assert math.isclose(base_stats.max, thread_stats.max, abs_tol=1e-4)
    assert math.isclose(base_stats.variance, thread_stats.variance, abs_tol=1e-4)
    assert math.isclose(base_stats.std_dev, thread_stats.std_dev, abs_tol=1e-4)
    assert math.isclose(base_stats.calibrated_mean, thread_stats.calibrated_mean, abs_tol=1e-4)


def test_multiprocess_vs_baseline(small_experiments: List[Experiment]) -> None:
    """Test that ProcessPoolExecutor yields identical results to Baseline."""
    base_stats = calculate_statistics_sequential(small_experiments)
    mp_stats = calculate_statistics_multiprocess(small_experiments, workers=2)

    assert base_stats.count == mp_stats.count
    assert math.isclose(base_stats.mean, mp_stats.mean, abs_tol=1e-4)
    assert math.isclose(base_stats.min, mp_stats.min, abs_tol=1e-4)
    assert math.isclose(base_stats.max, mp_stats.max, abs_tol=1e-4)
    assert math.isclose(base_stats.variance, mp_stats.variance, abs_tol=1e-4)
    assert math.isclose(base_stats.std_dev, mp_stats.std_dev, abs_tol=1e-4)
    assert math.isclose(base_stats.calibrated_mean, mp_stats.calibrated_mean, abs_tol=1e-4)


def test_race_condition_and_lock() -> None:
    """Test that race condition occurs without lock and Lock guarantees thread safety."""
    unsafe_cnt, safe_cnt = run_race_condition_experiment(iterations_per_thread=500, threads_count=4)
    expected = 2_000
    assert unsafe_cnt < expected, f"Expected race condition to cause loss, but got {unsafe_cnt}"
    assert safe_cnt == expected, f"Safe accumulator failed to reach {expected}, got {safe_cnt}"


def test_concurrent_io_loading(small_experiments: List[Experiment], temp_dir: Path) -> None:
    """Test sequential vs threaded batch file loading consistency."""
    batch_paths = export_experiment_batches(small_experiments, temp_dir, num_batches=4)
    assert len(batch_paths) == 4

    seq_loaded = load_datasets_sequential(batch_paths)
    thread_loaded = load_datasets_threadpool(batch_paths, max_workers=2)

    assert len(seq_loaded) == len(small_experiments)
    assert len(thread_loaded) == len(small_experiments)

    seq_ids = sorted(e.id for e in seq_loaded)
    thread_ids = sorted(e.id for e in thread_loaded)
    assert seq_ids == thread_ids
