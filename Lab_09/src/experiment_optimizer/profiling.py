"""Profiling utilities using cProfile and tracemalloc."""

from __future__ import annotations

import cProfile
import io
import pstats
import time
import tracemalloc
from typing import Any, Callable, Dict, List, Tuple


def measure_execution_time(
    func: Callable[..., Any],
    *args: Any,
    repeats: int = 5,
    **kwargs: Any,
) -> List[float]:
    """Measure function execution time over multiple independent repeats using high-precision perf_counter."""
    durations: List[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        func(*args, **kwargs)
        t1 = time.perf_counter()
        durations.append(t1 - t0)
    return durations


def profile_with_cprofile(
    func: Callable[..., Any],
    *args: Any,
    top_n: int = 10,
    **kwargs: Any,
) -> Tuple[Any, List[Dict[str, Any]], str]:
    """Profile function with cProfile, extracting structured metrics and formatted text summary."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(top_n)
    text_summary = stream.getvalue()

    # Extract top functions as structured dictionaries
    structured_data: List[Dict[str, Any]] = []
    # stats.stats format: (filename, lineno, func_name) -> (cc, nc, tt, ct, callers)
    sorted_func_list = sorted(stats.stats.items(), key=lambda item: item[1][3], reverse=True)

    for (fn, lno, func_name), (cc, nc, tt, ct, _) in sorted_func_list[:top_n]:
        short_fn = fn.split("\\")[-1].split("/")[-1]
        structured_data.append(
            {
                "function": f"{short_fn}:{lno}({func_name})",
                "ncalls": nc,
                "tottime": round(tt, 6),
                "cumtime": round(ct, 6),
                "percall_tot": round(tt / nc, 8) if nc else 0.0,
                "percall_cum": round(ct / nc, 8) if nc else 0.0,
            }
        )

    return result, structured_data, text_summary


def profile_with_tracemalloc(
    func: Callable[..., Any],
    *args: Any,
    top_allocations: int = 5,
    **kwargs: Any,
) -> Tuple[Any, float, float, List[Dict[str, Any]]]:
    """Profile memory allocations using tracemalloc.

    Returns:
        (result, current_memory_kb, peak_memory_kb, top_traces)
    """
    tracemalloc.start()
    tracemalloc.reset_peak()

    result = func(*args, **kwargs)

    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    current_kb = round(current_bytes / 1024, 2)
    peak_kb = round(peak_bytes / 1024, 2)

    top_traces: List[Dict[str, Any]] = []
    top_stats = snapshot.statistics("lineno")[:top_allocations]
    for stat in top_stats:
        frame = stat.traceback[0]
        short_fn = frame.filename.split("\\")[-1].split("/")[-1]
        top_traces.append(
            {
                "location": f"{short_fn}:{frame.lineno}",
                "size_kb": round(stat.size / 1024, 2),
                "count": stat.count,
            }
        )

    return result, current_kb, peak_kb, top_traces
