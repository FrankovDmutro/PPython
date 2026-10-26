"""Concurrency, Multiprocessing, and Thread Synchronization."""

from __future__ import annotations

import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from threading import Lock, Thread
from typing import Callable, List, Sequence, Tuple, Union

from .analytics import calibrate_sensor_value
from .dataset import load_experiments_from_file
from .models import Experiment, ExperimentStatistics


class UnsafeMetricAccumulator:
    """Demonstrates a race condition on an unprotected shared counter."""

    def __init__(self) -> None:
        self.counter: int = 0
        self.total_sum: float = 0.0

    def add(self, value: float) -> None:
        # Deliberate context switch yield between read and write to trigger race condition
        current_cnt = self.counter
        current_sum = self.total_sum
        time.sleep(0)  # Yield GIL to peer thread
        self.counter = current_cnt + 1
        self.total_sum = current_sum + value


class SafeMetricAccumulator:
    """Thread-safe metric accumulator protected by a threading.Lock."""

    def __init__(self) -> None:
        self.counter: int = 0
        self.total_sum: float = 0.0
        self._lock = Lock()

    def add(self, value: float) -> None:
        with self._lock:
            current_cnt = self.counter
            current_sum = self.total_sum
            time.sleep(0)  # Thread-safe under Lock protection
            self.counter = current_cnt + 1
            self.total_sum = current_sum + value


def run_race_condition_experiment(
    iterations_per_thread: int = 1_000,
    threads_count: int = 4,
) -> Tuple[int, int]:
    """Run concurrent increments using both Unsafe and Safe accumulators.

    Returns:
        (unsafe_result, safe_result)
    """
    unsafe_acc = UnsafeMetricAccumulator()
    safe_acc = SafeMetricAccumulator()

    def worker_unsafe() -> None:
        for _ in range(iterations_per_thread):
            unsafe_acc.add(1.0)

    def worker_safe() -> None:
        for _ in range(iterations_per_thread):
            safe_acc.add(1.0)

    # 1. Run unsafe threads
    threads: List[Thread] = []
    for _ in range(threads_count):
        t = Thread(target=worker_unsafe)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # 2. Run safe threads
    threads.clear()
    for _ in range(threads_count):
        t = Thread(target=worker_safe)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return unsafe_acc.counter, safe_acc.counter


# Worker function for parallel processing (must be top-level for Windows multiprocessing pickle)
def _chunk_statistics_worker(
    chunk: Sequence[float],
) -> Tuple[int, float, float, float, float, float]:
    """Process a chunk of numbers, returning:

    (count, sum_x, sum_x2, min_val, max_val, calibrated_sum).
    """
    if not chunk:
        return 0, 0.0, 0.0, 0.0, 0.0, 0.0

    n = len(chunk)
    sum_x = 0.0
    sum_x2 = 0.0
    min_val = chunk[0]
    max_val = chunk[0]
    calibrated_sum = 0.0

    for x in chunk:
        sum_x += x
        sum_x2 += x * x
        if x < min_val:
            min_val = x
        if x > max_val:
            max_val = x
        calibrated_sum += calibrate_sensor_value(x)

    return n, sum_x, sum_x2, min_val, max_val, calibrated_sum


def _split_into_chunks(data: Sequence[float], num_chunks: int) -> List[List[float]]:
    """Split data sequence into roughly equal chunks."""
    k, m = divmod(len(data), num_chunks)
    chunks: List[List[float]] = []
    for i in range(num_chunks):
        start = i * k + min(i, m)
        end = (i + 1) * k + min(i + 1, m)
        if start < end:
            chunks.append(list(data[start:end]))
    return chunks


def calculate_statistics_threads(
    data: Sequence[Union[Experiment, float]],
    workers: int = 4,
) -> ExperimentStatistics:
    """Calculate statistics using ThreadPoolExecutor (CPU-bound concurrency subject to GIL)."""
    if not data:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    if isinstance(data[0], Experiment):
        values = [e.result for e in data]  # type: ignore
    else:
        values = list(data)  # type: ignore

    chunks = _split_into_chunks(values, workers)
    if not chunks:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_chunk_statistics_worker, chunks))

    return _combine_chunk_statistics(results)


def calculate_statistics_multiprocess(
    data: Sequence[Union[Experiment, float]],
    workers: int = 4,
    chunksize: int | None = None,
) -> ExperimentStatistics:
    """Calculate statistics using ProcessPoolExecutor (Bypasses GIL for true CPU parallelism)."""
    if not data:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    if isinstance(data[0], Experiment):
        values = [e.result for e in data]  # type: ignore
    else:
        values = list(data)  # type: ignore

    # Split into chunks (default: 4 chunks per worker for optimal load balancing)
    num_chunks = workers * 4 if chunksize is None else max(1, len(values) // chunksize)
    chunks = _split_into_chunks(values, num_chunks)
    if not chunks:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_chunk_statistics_worker, chunks))

    return _combine_chunk_statistics(results)


def _combine_chunk_statistics(
    chunk_results: List[Tuple[int, float, float, float, float, float]],
) -> ExperimentStatistics:
    """Combine partial results from chunks into global descriptive statistics."""
    total_count = 0
    total_sum = 0.0
    total_sum_sq = 0.0
    global_min = float("inf")
    global_max = float("-inf")
    total_calibrated = 0.0

    for n, sum_x, sum_x2, min_v, max_v, calib_s in chunk_results:
        if n == 0:
            continue
        total_count += n
        total_sum += sum_x
        total_sum_sq += sum_x2
        if min_v < global_min:
            global_min = min_v
        if max_v > global_max:
            global_max = max_v
        total_calibrated += calib_s

    if total_count == 0:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    mean = total_sum / total_count
    # Population variance: E[X^2] - (E[X])^2
    variance = max(0.0, (total_sum_sq / total_count) - (mean * mean))
    std_dev = math.sqrt(variance)
    calibrated_mean = total_calibrated / total_count

    return ExperimentStatistics(
        count=total_count,
        mean=round(mean, 6),
        min=round(global_min, 6),
        max=round(global_max, 6),
        variance=round(variance, 6),
        std_dev=round(std_dev, 6),
        calibrated_mean=round(calibrated_mean, 6),
    )


# I/O Bound concurrent loading
def load_datasets_sequential(filepaths: Sequence[Path | str]) -> List[Experiment]:
    """Load multiple experiment files sequentially."""
    all_experiments: List[Experiment] = []
    for fp in filepaths:
        all_experiments.extend(load_experiments_from_file(fp))
    return all_experiments


def load_datasets_threadpool(
    filepaths: Sequence[Path | str],
    max_workers: int = 4,
) -> List[Experiment]:
    """Load multiple experiment files concurrently using ThreadPoolExecutor (I/O speedup)."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        batches = list(executor.map(load_experiments_from_file, filepaths))

    all_experiments: List[Experiment] = []
    for batch in batches:
        all_experiments.extend(batch)
    return all_experiments
