"""Extrapolation logic for projecting performance at scale"""

import warnings
from typing import Dict

from .config import PipelineScopeConfig
from .stats import FunctionKey, FunctionStats, ProfilingResult

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


class ExtrapolatedStats:
    """Extrapolated statistics for a function"""

    def __init__(self, original_stats: FunctionStats, scale_factor: float):
        self.observed_calls = original_stats.call_count
        self.observed_time_ms = original_stats.total_time_ms
        self.observed_self_time_ms = original_stats.self_time_ms
        self.projected_calls = int(original_stats.call_count * scale_factor)
        self.projected_time_ms = original_stats.total_time_ms * scale_factor
        self.projected_self_time_ms = original_stats.self_time_ms * scale_factor
        self.avg_cpu_percent = original_stats.avg_cpu_percent
        self.peak_memory_mb = original_stats.peak_memory_mb
        self.avg_gpu_utilization = original_stats.avg_gpu_utilization
        self.peak_gpu_memory_mb = original_stats.peak_gpu_memory_mb
        self.percentage_of_total = 0.0


def extrapolate(
    profiling_result: ProfilingResult, config: PipelineScopeConfig
) -> Dict[FunctionKey, ExtrapolatedStats]:
    """
    Extrapolate profiling results to expected scale using linear scaling.

    Args:
        profiling_result: Results from profiling
        config: Configuration with sample_size and expected_size

    Returns:
        Dictionary mapping function keys to extrapolated statistics
