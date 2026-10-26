"""Experiment Manager & Optimization Suite (Lab 09, Variant 15)."""

from .analytics import (
    calculate_statistics_numpy,
    calculate_statistics_sequential,
    filter_by_range_numpy,
    filter_by_range_sequential,
    group_by_researcher_sequential,
)
from .caching import ExperimentStatsCache, cached_heavy_computation
from .dataset import (
    export_experiment_batches,
    generate_experiments,
    generate_researchers,
    load_experiments_from_file,
)
from .models import Experiment, ExperimentStatistics, Researcher
from .parallel import (
    SafeMetricAccumulator,
    UnsafeMetricAccumulator,
    calculate_statistics_multiprocess,
    calculate_statistics_threads,
    load_datasets_sequential,
    load_datasets_threadpool,
    run_race_condition_experiment,
)
from .profiling import (
    measure_execution_time,
    profile_with_cprofile,
    profile_with_tracemalloc,
)

__all__ = [
    "Researcher",
    "Experiment",
    "ExperimentStatistics",
    "generate_researchers",
    "generate_experiments",
    "export_experiment_batches",
    "load_experiments_from_file",
    "calculate_statistics_sequential",
    "filter_by_range_sequential",
    "group_by_researcher_sequential",
    "calculate_statistics_numpy",
    "filter_by_range_numpy",
    "UnsafeMetricAccumulator",
    "SafeMetricAccumulator",
    "run_race_condition_experiment",
    "calculate_statistics_threads",
    "calculate_statistics_multiprocess",
    "load_datasets_sequential",
    "load_datasets_threadpool",
    "ExperimentStatsCache",
    "cached_heavy_computation",
    "measure_execution_time",
    "profile_with_cprofile",
    "profile_with_tracemalloc",
]
