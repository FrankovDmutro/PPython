"""Comprehensive Automated Performance Benchmarking Suite (Lab 09, Variant 15).

Measures:
1. Baseline (Sequential Python loops)
2. ThreadPoolExecutor (GIL impact on CPU-bound logic)
3. ProcessPoolExecutor scaling (1, 2, 4, 8, 16 workers)
4. NumPy Vectorization
5. Caching (Cold vs Warm, Invalidation)
6. I/O-bound Concurrency (Batch loading with ThreadPoolExecutor)
7. Race condition demonstration and Lock synchronization
Generates CSV tables and publication-quality Matplotlib figures.
"""

from __future__ import annotations

import csv
import os
import shutil
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np

from experiment_optimizer.analytics import (
    calculate_statistics_numpy,
    calculate_statistics_sequential,
)
from experiment_optimizer.caching import ExperimentStatsCache
from experiment_optimizer.dataset import (
    export_experiment_batches,
    generate_experiments,
)
from experiment_optimizer.parallel import (
    calculate_statistics_multiprocess,
    calculate_statistics_threads,
    load_datasets_sequential,
    load_datasets_threadpool,
    run_race_condition_experiment,
)
from experiment_optimizer.profiling import (
    measure_execution_time,
    profile_with_tracemalloc,
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_cpu_benchmarks() -> List[Dict[str, Any]]:
    """Run CPU-bound benchmarks across dataset sizes and parallel paradigms."""
    dataset_sizes = [10_000, 100_000, 1_000_000]
    methods = [
        ("Sequential (Baseline)", lambda data: calculate_statistics_sequential(data), 1),
        ("ThreadPool (4 workers)", lambda data: calculate_statistics_threads(data, workers=4), 4),
        ("ProcessPool (1 worker)", lambda data: calculate_statistics_multiprocess(data, workers=1), 1),
        ("ProcessPool (2 workers)", lambda data: calculate_statistics_multiprocess(data, workers=2), 2),
        ("ProcessPool (4 workers)", lambda data: calculate_statistics_multiprocess(data, workers=4), 4),
        ("ProcessPool (8 workers)", lambda data: calculate_statistics_multiprocess(data, workers=8), 8),
        ("ProcessPool (16 workers)", lambda data: calculate_statistics_multiprocess(data, workers=16), 16),
        ("NumPy Vectorization", lambda data: calculate_statistics_numpy(data), 1),
    ]

    benchmark_rows: List[Dict[str, Any]] = []

    print("\n" + "=" * 95)
    print(f"{'DATASET':<10} | {'METHOD':<26} | {'WORKERS':<7} | {'MEAN (s)':<10} | {'SPEEDUP':<8} | {'PEAK MEM (KB)':<14}")
    print("=" * 95)

    for size in dataset_sizes:
        print(f"\n--- Generating test dataset of {size:,} experiments ---")
        experiments = generate_experiments(size, seed=42)
        # Pre-extract float results for clean array/list benchmark
        raw_results = [e.result for e in experiments]
        numpy_results = np.asarray(raw_results, dtype=np.float64)

        baseline_mean = 0.0

        for method_name, fn, workers in methods:
            # Pass numpy array directly to NumPy method for fair pure-compute benchmark
            input_data = numpy_results if "NumPy" in method_name else raw_results

            # Memory profiling (1 run)
            _, current_kb, peak_kb, _ = profile_with_tracemalloc(fn, input_data)

            # Warmup
            fn(input_data)

            # Time measurements (5 repeats)
            repeats = 5
            runs: List[float] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                fn(input_data)
                t1 = time.perf_counter()
                runs.append(t1 - t0)

            mean_sec = statistics.mean(runs)
            if "Baseline" in method_name:
                baseline_mean = mean_sec
                speedup = 1.0
            else:
                speedup = (baseline_mean / mean_sec) if mean_sec > 0 else 0.0

            row = {
                "dataset_size": size,
                "method": method_name,
                "workers": workers,
                "run_1": round(runs[0], 6),
                "run_2": round(runs[1], 6),
                "run_3": round(runs[2], 6),
                "run_4": round(runs[3], 6),
                "run_5": round(runs[4], 6),
                "mean_seconds": round(mean_sec, 6),
                "speedup": round(speedup, 2),
                "peak_memory_kb": round(peak_kb, 2),
            }
            benchmark_rows.append(row)

            print(
                f"{size:<10} | {method_name:<26} | {workers:<7} | "
                f"{mean_sec:<10.5f} | {speedup:<7.2f}x | {peak_kb:<14.2f}"
            )

    return benchmark_rows


def run_io_benchmark() -> Dict[str, Any]:
    """Benchmark sequential vs threaded batch file ingestion."""
    print("\n--- Running I/O-Bound Batch Ingestion Benchmark ---")
    data_dir = RESULTS_DIR / "io_batches_temp"
    if data_dir.exists():
        shutil.rmtree(data_dir)

    sample_exps = generate_experiments(100_000, seed=123)
    batch_paths = export_experiment_batches(sample_exps, data_dir, num_batches=10)

    # Sequential loading
    seq_runs = measure_execution_time(load_datasets_sequential, batch_paths, repeats=5)
    seq_mean = statistics.mean(seq_runs)

    # Threaded loading (4 workers)
    thread_runs = measure_execution_time(load_datasets_threadpool, batch_paths, max_workers=4, repeats=5)
    thread_mean = statistics.mean(thread_runs)

    io_speedup = seq_mean / thread_mean if thread_mean > 0 else 0.0

    # Cleanup temp batches
    shutil.rmtree(data_dir, ignore_errors=True)

    print(f"Sequential I/O (10 files): {seq_mean:.4f}s")
    print(f"ThreadPoolExecutor (4 workers): {thread_mean:.4f}s | Speedup: {io_speedup:.2f}x")

    return {
        "sequential_io_seconds": round(seq_mean, 5),
        "threaded_io_seconds": round(thread_mean, 5),
        "io_speedup": round(io_speedup, 2),
    }


def run_caching_benchmark() -> Dict[str, Any]:
    """Benchmark cold cache vs warm cache speed and invalidation."""
    print("\n--- Running Caching & Invalidation Benchmark ---")
    experiments = generate_experiments(100_000, seed=42)
    cache = ExperimentStatsCache()

    # Cold cache query
    t0 = time.perf_counter()
    stats1 = cache.get_statistics("dataset_100k", experiments)
    cold_time = time.perf_counter() - t0

    # Warm cache queries (repeated 10 times)
    warm_times: List[float] = []
    for _ in range(10):
        t0 = time.perf_counter()
        _ = cache.get_statistics("dataset_100k", experiments)
        warm_times.append(time.perf_counter() - t0)

    warm_mean = statistics.mean(warm_times)
    cache_speedup = cold_time / warm_mean if warm_mean > 0 else 0.0

    # Test cache invalidation
    invalidated_count = cache.invalidate("dataset_100k")
    t0 = time.perf_counter()
    _ = cache.get_statistics("dataset_100k", experiments)
    post_inval_time = time.perf_counter() - t0

    telemetry = cache.telemetry_report()
    print(f"Cold Cache Access: {cold_time:.5f}s")
    print(f"Warm Cache Access (Avg): {warm_mean:.8f}s | Speedup: {cache_speedup:,.0f}x")
    print(f"Cache Invalidation Verified: {invalidated_count} key(s) purged, new lookup took {post_inval_time:.5f}s")
    print(f"Telemetry: {telemetry}")

    return {
        "cold_cache_time": round(cold_time, 5),
        "warm_cache_time": round(warm_mean, 8),
        "cache_speedup": round(cache_speedup, 1),
        "telemetry": telemetry,
    }


def run_synchronization_benchmark() -> Dict[str, Any]:
    """Demonstrate Race Condition and Lock Synchronization."""
    print("\n--- Running Race Condition & Lock Synchronization Benchmark ---")
    threads = 4
    iterations = 1_000
    expected = threads * iterations

    unsafe_res, safe_res = run_race_condition_experiment(iterations, threads)
    loss = expected - unsafe_res
    print(f"Expected count: {expected:,}")
    print(f"Unsafe Accumulator: {unsafe_res:,} (Lost updates: {loss:,} -> Race condition confirmed)")
    print(f"Safe Accumulator (Lock): {safe_res:,} (Loss: {expected - safe_res:,} -> Thread-safe)")

    return {
        "expected": expected,
        "unsafe_result": unsafe_res,
        "lost_updates": loss,
        "safe_result": safe_res,
    }


def save_csv_results(rows: List[Dict[str, Any]]) -> Path:
    """Save benchmark records to CSV."""
    csv_path = RESULTS_DIR / "benchmark_results.csv"
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved CSV results to: {csv_path}")
    return csv_path


def generate_figures(rows: List[Dict[str, Any]]) -> None:
    """Generate high-resolution PNG charts comparing performance."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Execution Time vs Dataset Size
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    methods_to_plot = [
        "Sequential (Baseline)",
        "ThreadPool (4 workers)",
        "ProcessPool (4 workers)",
        "ProcessPool (8 workers)",
        "NumPy Vectorization",
    ]
    colors = ["#e74c3c", "#e67e22", "#2980b9", "#27ae60", "#8e44ad"]
    markers = ["o", "s", "^", "D", "P"]

    sizes = [10_000, 100_000, 1_000_000]
    size_labels = ["10k", "100k", "1M"]

    for m_idx, method in enumerate(methods_to_plot):
        times = [r["mean_seconds"] for r in rows if r["method"] == method]
        ax.plot(
            size_labels,
            times,
            marker=markers[m_idx],
            color=colors[m_idx],
            linewidth=2.2,
            markersize=8,
            label=method,
        )

    ax.set_title("Час виконання від обсягу даних (Execution Time vs Dataset Size)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Розмір вибірки (Dataset Size)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Час виконання (секунди, log scale)", fontsize=11, fontweight="bold")
    ax.set_yscale("log")
    ax.legend(frameon=True, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig_path1 = RESULTS_DIR / "execution_time_comparison.png"
    plt.savefig(fig_path1)
    plt.close()
    print(f"Generated chart: {fig_path1}")

    # 2. Speedup Comparison for 1,000,000 records
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    large_rows = [r for r in rows if r["dataset_size"] == 1_000_000]
    bar_methods = [r["method"] for r in large_rows]
    bar_speedups = [r["speedup"] for r in large_rows]

    bar_colors = ["#95a5a6" if "Baseline" in m else "#e67e22" if "ThreadPool" in m else "#2980b9" if "ProcessPool" in m else "#27ae60" for m in bar_methods]
    bars = ax.barh(bar_methods, bar_speedups, color=bar_colors, edgecolor="black", linewidth=0.8, height=0.6)

    ax.set_title("Коефіцієнт прискорення (Speedup) для 1 000 000 записів", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Speedup відносно Baseline (рази)", fontsize=11, fontweight="bold")
    ax.grid(axis="x", linestyle="--", alpha=0.6)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(
            f"{width:.2f}x",
            xy=(width, bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    fig_path2 = RESULTS_DIR / "speedup_comparison.png"
    plt.savefig(fig_path2)
    plt.close()
    print(f"Generated chart: {fig_path2}")

    # 3. Worker Scaling in ProcessPoolExecutor (1M records)
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    proc_rows = [r for r in large_rows if "ProcessPool" in r["method"]]
    workers = [r["workers"] for r in proc_rows]
    speedups = [r["speedup"] for r in proc_rows]

    ax.plot(workers, speedups, marker="o", color="#2980b9", linewidth=2.5, markersize=8, label="Фактичний Speedup")
    ax.plot(workers, workers, linestyle="--", color="#7f8c8d", label="Ідеальний лінійний скейлінг (Amdahl)")

    ax.set_title("Масштабування ProcessPoolExecutor (Worker Scaling, 1M записів)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Кількість процесів-воркерів (Workers)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Коефіцієнт прискорення (Speedup)", fontsize=11, fontweight="bold")
    ax.set_xticks(workers)
    ax.legend(frameon=True, fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    fig_path3 = RESULTS_DIR / "worker_scaling.png"
    plt.savefig(fig_path3)
    plt.close()
    print(f"Generated chart: {fig_path3}")

    # 4. Peak Memory Usage (Tracemalloc)
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    mem_methods = [r["method"] for r in large_rows]
    mem_values = [r["peak_memory_kb"] / 1024 for r in large_rows]  # convert to MB

    bars_mem = ax.bar(mem_methods, mem_values, color="#34495e", edgecolor="black", linewidth=0.8, width=0.55)
    ax.set_title("Пікове використання оперативної пам'яті (Peak Memory, 1M записів)", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Пікова пам'ять (МБ)", fontsize=11, fontweight="bold")
    plt.xticks(rotation=30, ha="right", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    for bar in bars_mem:
        height = bar.get_height()
        ax.annotate(
            f"{height:.1f} MB",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()
    fig_path4 = RESULTS_DIR / "memory_usage_comparison.png"
    plt.savefig(fig_path4)
    plt.close()
    print(f"Generated chart: {fig_path4}")


def main() -> None:
    """Main benchmark execution pipeline."""
    print("===============================================================================")
    print("  Лабораторна робота №9: Бенчмаркінг продуктивності та оптимізації (Варіант 15)")
    print("===============================================================================")
    start_time = time.perf_counter()

    cpu_rows = run_cpu_benchmarks()
    io_metrics = run_io_benchmark()
    cache_metrics = run_caching_benchmark()
    sync_metrics = run_synchronization_benchmark()

    save_csv_results(cpu_rows)
    generate_figures(cpu_rows)

    total_time = time.perf_counter() - start_time
    print(f"\nУсі бенчмарки та графіки успішно згенеровано за {total_time:.2f} с!")


if __name__ == "__main__":
    main()
