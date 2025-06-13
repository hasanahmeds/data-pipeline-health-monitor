"""JSON serializer for profiling data"""

import json
import warnings
from pathlib import Path
from typing import Dict

from ..core.extrapolation import ExtrapolatedStats
from ..core.stats import FunctionKey, ProfilingResult

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


def serialize_profiling_data(
    profiling_result: ProfilingResult,
    extrapolated_stats: Dict[FunctionKey, ExtrapolatedStats],
    output_path: Path,
) -> None:
    """
    Serialize profiling data to JSON file.

    Args:
        profiling_result: Profiling results
        extrapolated_stats: Extrapolated statistics
        output_path: Path to write JSON file
    """
    data = {
        "metadata": {
            "total_runtime_ms": round(profiling_result.total_runtime_ms, 2),
            "start_timestamp": profiling_result.start_timestamp,
            "end_timestamp": profiling_result.end_timestamp,
            "total_functions": len(profiling_result.function_stats),
        },
        "functions": [],
        "call_edges": [],
    }

    for func_key, func_stats in profiling_result.function_stats.items():
        func_data = {
            "module": func_key.module,
            "filename": func_key.filename,
            "funcname": func_key.funcname,
            "lineno": func_key.lineno,
            "classname": func_key.classname,
            "display_name": func_key.display_name,
            "call_count": func_stats.call_count,
            "total_time_ms": round(func_stats.total_time_ms, 2),
            "self_time_ms": round(func_stats.self_time_ms, 2),
            "avg_time_ms": round(func_stats.avg_time_ms, 2),
            "avg_cpu_percent": round(func_stats.avg_cpu_percent, 2),
            "peak_memory_mb": round(func_stats.peak_memory_mb, 2),
        }

        extra = extrapolated_stats.get(func_key)
        if extra:
            func_data["projected_calls"] = extra.projected_calls
            func_data["projected_time_ms"] = round(extra.projected_time_ms, 2)
            func_data["projected_self_time_ms"] = round(extra.projected_self_time_ms, 2)
            func_data["percentage_of_total"] = round(extra.percentage_of_total, 2)

        data["functions"].append(func_data)

    for (caller_key, callee_key), edge in profiling_result.call_edges.items():
        edge_data = {
            "caller": caller_key.display_name,
            "callee": callee_key.display_name,
            "call_count": edge.call_count,
            "total_time_ms": round(edge.total_time_ms, 2),
            "avg_time_ms": round(edge.avg_time_ms, 2),
        }
        data["call_edges"].append(edge_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=None, separators=(",", ":"))
