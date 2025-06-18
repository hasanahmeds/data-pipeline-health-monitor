"""Analyzer for extracting hotspots and aggregating metrics"""

import heapq
import warnings
from collections import defaultdict
from typing import Dict, List

from ..core.extrapolation import ExtrapolatedStats
from ..core.stats import FunctionKey, FunctionStats, ProfilingResult

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


def _should_include_function(func_key: FunctionKey) -> bool:
    if not func_key.funcname or not func_key.funcname.strip():
        return False
    if func_key.funcname.startswith("<"):
        return False
    if func_key.is_stdlib:
        return False
    return True


class HotspotFunction:
    """Represents a hotspot function with all relevant metrics"""

    def __init__(
        self, func_key: FunctionKey, stats: FunctionStats, extrapolated: ExtrapolatedStats
    ):
        self.func_key = func_key
        self.stats = stats
        self.extrapolated = extrapolated

        if func_key.classname:
            self.display_name = f"{func_key.stage}.{func_key.classname}.{func_key.funcname}"
        else:
            self.display_name = f"{func_key.stage}.{func_key.funcname}"

        self.module = func_key.module
        self.classname = func_key.classname

        self.call_count = stats.call_count
        self.total_time_ms = stats.total_time_ms
        self.self_time_ms = stats.self_time_ms
        self.avg_time_ms = stats.avg_time_ms

        self.projected_calls = extrapolated.projected_calls
        self.projected_time_ms = extrapolated.projected_time_ms
        self.projected_self_time_ms = extrapolated.projected_self_time_ms
        self.percentage_of_total = extrapolated.percentage_of_total

        self.avg_cpu_percent = stats.avg_cpu_percent
        self.peak_memory_mb = stats.peak_memory_mb
        self.avg_gpu_utilization = stats.avg_gpu_utilization
        self.peak_gpu_memory_mb = stats.peak_gpu_memory_mb

        if self.avg_gpu_utilization and len(self.avg_gpu_utilization) > 0:
            self._avg_gpu_utilization = round(
                sum(self.avg_gpu_utilization) / len(self.avg_gpu_utilization), 2
            )
        else:
            self._avg_gpu_utilization = 0.0

        if self.peak_gpu_memory_mb and len(self.peak_gpu_memory_mb) > 0:
            self._peak_gpu_memory_mb = round(max(self.peak_gpu_memory_mb), 2)
        else:
            self._peak_gpu_memory_mb = 0.0

    def __repr__(self):
        return (
            f"HotspotFunction("
            f"display_name={self.display_name!r}, "
            f"module={self.module!r}, "
            f"classname={self.classname!r}, "
            f"call_count={self.call_count}, "
            f"total_time_ms={self.total_time_ms:.2f}, "
            f"self_time_ms={self.self_time_ms:.2f}, "
            f"avg_time_ms={self.avg_time_ms:.2f}, "
            f"projected_calls={self.projected_calls}, "
            f"projected_time_ms={self.projected_time_ms:.2f}, "
            f"projected_self_time_ms={self.projected_self_time_ms:.2f}, "
            f"percentage_of_total={self.percentage_of_total:.2f}, "
            f"avg_cpu_percent={self.avg_cpu_percent:.2f}, "
            f"peak_memory_mb={self.peak_memory_mb:.2f}, "
            f"avg_gpu_utilization={self.avg_gpu_utilization}, "
            f"peak_gpu_memory_mb={self.peak_gpu_memory_mb}"
            f")"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/template"""
        return {
            "display_name": self.display_name,
            "module": self.module,
            "classname": self.classname or "",
            "call_count": self.call_count,
            "total_time_ms": round(self.total_time_ms, 2),
            "self_time_ms": round(self.self_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "projected_calls": self.projected_calls,
            "projected_time_ms": round(self.projected_time_ms, 2),
            "projected_self_time_ms": round(self.projected_self_time_ms, 2),
            "percentage": round(self.percentage_of_total, 2),
            "avg_cpu_percent": round(self.avg_cpu_percent, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "avg_gpu_utilization": self._avg_gpu_utilization,
            "peak_gpu_memory_mb": self._peak_gpu_memory_mb,
        }


class ModuleAggregate:
    """Aggregated metrics for a module/script"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.function_count = 0
        self.total_calls = 0
        self.total_time_ms = 0.0
        self.projected_time_ms = 0.0
        self.percentage_of_total = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON/template"""
        return {
            "module_name": self.module_name,
            "function_count": self.function_count,
            "total_calls": self.total_calls,
            "total_time_ms": round(self.total_time_ms, 2),
            "projected_time_ms": round(self.projected_time_ms, 2),
            "percentage": round(self.percentage_of_total, 2),
        }


def extract_hotspots(
    profiling_result: ProfilingResult,
    extrapolated_stats: Dict[FunctionKey, ExtrapolatedStats],
    top_n: int = 5,
) -> List[HotspotFunction]:
    hotspots = []

    for func_key, func_stats in profiling_result.function_stats.items():
        if func_key not in extrapolated_stats:
            continue
        if not _should_include_function(func_key):
            continue

        hotspot = HotspotFunction(func_key, func_stats, extrapolated_stats[func_key])
        if hotspot.display_name:
            heapq.heappush(hotspots, (-hotspot.projected_self_time_ms, id(hotspot), hotspot))
            if len(hotspots) > top_n:
                heapq.heappop(hotspots)
    return sorted((h[2] for h in hotspots), key=lambda h: h.projected_self_time_ms, reverse=True)


def aggregate_by_module(
    profiling_result: ProfilingResult, extrapolated_stats: Dict[FunctionKey, ExtrapolatedStats]
) -> List[ModuleAggregate]:
    """
    Aggregate metrics by module/script.
    """
    module_data = defaultdict(
        lambda: {
            "function_count": 0,
            "total_calls": 0,
            "total_time_ms": 0.0,
            "projected_time_ms": 0.0,
        }
    )

    total_projected = 0.0
    for func_key, func_stats in profiling_result.function_stats.items():
        if not _should_include_function(func_key):
            continue

        module = func_key.module
        module_data[module]["function_count"] += 1
        module_data[module]["total_calls"] += func_stats.call_count
        module_data[module]["total_time_ms"] += func_stats.total_time_ms

        if func_key in extrapolated_stats:
            projected = extrapolated_stats[func_key].projected_time_ms
            module_data[module]["projected_time_ms"] += projected
            total_projected += projected

    aggregates = []
    for module_name, data in module_data.items():
        if not module_name:
            continue

        agg = ModuleAggregate(module_name)
        agg.function_count = data["function_count"]
        agg.total_calls = data["total_calls"]
        agg.total_time_ms = data["total_time_ms"]
        agg.projected_time_ms = data["projected_time_ms"]

        if total_projected > 0:
            agg.percentage_of_total = (data["projected_time_ms"] / total_projected) * 100

        aggregates.append(agg)

    aggregates.sort(key=lambda a: a.projected_time_ms, reverse=True)

    return aggregates


def get_all_functions(
    profiling_result: ProfilingResult, extrapolated_stats: Dict[FunctionKey, ExtrapolatedStats]
) -> List[HotspotFunction]:
    all_functions = []

    for func_key, func_stats in profiling_result.function_stats.items():
        if not _should_include_function(func_key):
            continue
        if func_key not in extrapolated_stats:
            continue

        hotspot = HotspotFunction(func_key, func_stats, extrapolated_stats[func_key])
        if hotspot.display_name:
            all_functions.append(hotspot)

    all_functions.sort(key=lambda h: h.projected_self_time_ms, reverse=True)
    return all_functions
