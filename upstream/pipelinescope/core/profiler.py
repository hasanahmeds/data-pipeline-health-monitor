"""Main profiler using sys.setprofile"""

import sys
import time
import warnings
from typing import Dict, Optional

from ..utils.logger import get_logger
from .config import PipelineScopeConfig
from .resource_monitor import ResourceMonitor
from .stats import CallEdge, FunctionKey, FunctionStats, ProfilingResult

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


class Profiler:
    """Main profiler using sys.setprofile"""

    def __init__(self, config: PipelineScopeConfig):
        self.config = config
        self.active = False

        self.function_stats: Dict[FunctionKey, FunctionStats] = {}
        self.call_edges: Dict[tuple, CallEdge] = {}
        self.call_stack = []

        self._func_key_cache = {}

        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

        self.resource_monitor = ResourceMonitor(
            enable_cpu=config.enable_cpu_monitoring, enable_gpu=config.enable_gpu_monitoring
        )
        self.logger = get_logger()
        self._ignore_set = frozenset(self.config.ignore_modules)

    def start(self):
        """Start profiling"""
        if self.active:
            return

        self.active = True
        self.start_time = time.time()
        sys.setprofile(self._profile_callback)

    def stop(self) -> Optional[ProfilingResult]:
        """Stop profiling and return results"""
        if not self.active:
            return None

        self.active = False
        self.end_time = time.time()
        sys.setprofile(None)
        self._finalize_resource_metrics()

        caller_children: Dict[FunctionKey, float] = {}
        for edge_key, edge in self.call_edges.items():
            caller = edge_key[0]
            caller_children[caller] = caller_children.get(caller, 0) + edge.total_time_ms

        for func_key, stats in self.function_stats.items():
            stats.self_time_ms = stats.total_time_ms - caller_children.get(func_key, 0)

        result = ProfilingResult(
            function_stats=self.function_stats.copy(),
            call_edges=self.call_edges.copy(),
            total_runtime_ms=(self.end_time - self.start_time) * 1000,
            start_timestamp=self.start_time,
            end_timestamp=self.end_time,
        )

        self.function_stats.clear()
        self.call_edges.clear()
        self.call_stack.clear()

        return result

    def _finalize_resource_metrics(self):
        """Finalize GPU metrics (called once in stop())"""
        for stats in self.function_stats.values():
            if not stats._resource_samples:
                continue

            snapshot = stats._resource_samples[-1]
            if snapshot.gpu_utilization:
                num_gpus = len(snapshot.gpu_utilization)
                stats.avg_gpu_utilization = [
                    sum(
                        s.gpu_utilization[i]
                        for s in stats._resource_samples
                        if len(s.gpu_utilization) > i
                    )
                    / len(stats._resource_samples)
                    for i in range(num_gpus)
                ]
                stats.peak_gpu_memory_mb = [
                    max(
                        (
                            s.gpu_memory_mb[i]
                            for s in stats._resource_samples
                            if len(s.gpu_memory_mb) > i
                        ),
                        default=0.0,
                    )
                    for i in range(num_gpus)
                ]

    def _profile_callback(self, frame, event, arg):
        """Callback for sys.setprofile"""
        if event == "call":
            self._on_call(frame)
        elif event == "return":
            self._on_return(frame)

    def _on_call(self, frame):
        func_key = self._get_function_key(frame)

        if self._should_ignore(func_key):
            return
