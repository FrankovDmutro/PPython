"""Analytics engine: Baseline Python loops vs NumPy vectorized implementation."""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Union

import numpy as np

from .models import Experiment, ExperimentStatistics


def calibrate_sensor_value(val: float) -> float:
    """CPU-bound calibration simulating high-order polynomial and trigonometric correction."""
    return 1.05 * val - 0.0002 * (val**2) + 0.1 * math.sin(val)


def calculate_statistics_sequential(
    data: Sequence[Union[Experiment, float]],
) -> ExperimentStatistics:
    """Calculate descriptive statistics and sensor calibration using pure Python loops (Baseline)."""
    if not data:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    # Extract numerical values
    if isinstance(data[0], Experiment):
        values = [e.result for e in data]  # type: ignore
    else:
        values = list(data)  # type: ignore

    n = len(values)
    total = 0.0
    min_val = values[0]
    max_val = values[0]

    for val in values:
        total += val
        if val < min_val:
            min_val = val
        if val > max_val:
            max_val = val

    mean = total / n

    # Variance and Standard Deviation
    var_sum = 0.0
    calibrated_sum = 0.0
    for val in values:
        diff = val - mean
        var_sum += diff * diff
        calibrated_sum += calibrate_sensor_value(val)

    variance = var_sum / n
    std_dev = math.sqrt(variance)
    calibrated_mean = calibrated_sum / n

    return ExperimentStatistics(
        count=n,
        mean=round(mean, 6),
        min=round(min_val, 6),
        max=round(max_val, 6),
        variance=round(variance, 6),
        std_dev=round(std_dev, 6),
        calibrated_mean=round(calibrated_mean, 6),
    )


def filter_by_range_sequential(
    experiments: Sequence[Experiment],
    min_val: float,
    max_val: float,
) -> List[Experiment]:
    """Filter experiments by result range using sequential list comprehension."""
    return [e for e in experiments if min_val <= e.result <= max_val]


def group_by_researcher_sequential(
    experiments: Sequence[Experiment],
) -> Dict[int, Dict[str, float]]:
    """Group experiments and compute statistics per researcher sequentially."""
    grouped: Dict[int, List[float]] = {}
    for exp in experiments:
        grouped.setdefault(exp.researcher_id, []).append(exp.result)

    result_stats: Dict[int, Dict[str, float]] = {}
    for r_id, vals in grouped.items():
        count = len(vals)
        s = sum(vals)
        mean = s / count if count else 0.0
        result_stats[r_id] = {
            "count": float(count),
            "mean": round(mean, 4),
            "min": round(min(vals), 4) if vals else 0.0,
            "max": round(max(vals), 4) if vals else 0.0,
        }
    return result_stats


def calculate_statistics_numpy(
    data: Union[np.ndarray, Sequence[Union[Experiment, float]]],
) -> ExperimentStatistics:
    """Calculate descriptive statistics and sensor calibration using NumPy vectorization."""
    if isinstance(data, np.ndarray):
        arr = data
    elif len(data) == 0:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    elif isinstance(data[0], Experiment):
        arr = np.fromiter((e.result for e in data), dtype=np.float64, count=len(data))  # type: ignore
    else:
        arr = np.asarray(data, dtype=np.float64)

    n = int(arr.size)
    if n == 0:
        return ExperimentStatistics(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    mean = float(np.mean(arr))
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    variance = float(np.var(arr))
    std_dev = float(np.std(arr))

    # Vectorized calibration: 1.05 * x - 0.0002 * (x**2) + 0.1 * sin(x)
    calibrated_arr = 1.05 * arr - 0.0002 * (arr**2) + 0.1 * np.sin(arr)
    calibrated_mean = float(np.mean(calibrated_arr))

    return ExperimentStatistics(
        count=n,
        mean=round(mean, 6),
        min=round(min_val, 6),
        max=round(max_val, 6),
        variance=round(variance, 6),
        std_dev=round(std_dev, 6),
        calibrated_mean=round(calibrated_mean, 6),
    )


def filter_by_range_numpy(
    results_array: np.ndarray,
    min_val: float,
    max_val: float,
) -> np.ndarray:
    """Filter numerical array by range using NumPy boolean masking."""
    mask = (results_array >= min_val) & (results_array <= max_val)
    return results_array[mask]
