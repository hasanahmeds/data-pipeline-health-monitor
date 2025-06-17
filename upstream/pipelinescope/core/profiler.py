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

        stats = self.function_stats.get(func_key)
        if stats is None:
            stats = FunctionStats(key=func_key)
            self.function_stats[func_key] = stats

        if stats.first_call_time is None:
            stats.first_call_time = time.time()

        stats.call_count += 1
        stats._active_calls += 1
        start_time = time.time()
        stats._sample_counter += 1

        if stats._sample_counter % 100 == 0:
            snapshot = self.resource_monitor.snapshot()
            stats._resource_samples.append(snapshot)

        if self.call_stack:
            caller_key = self.call_stack[-1][0]
            edge_key = (caller_key, func_key)
            if edge_key not in self.call_edges:
                self.call_edges[edge_key] = CallEdge(caller=caller_key, callee=func_key)
            self.call_edges[edge_key].call_count += 1

        self.call_stack.append((func_key, start_time))

    def _on_return(self, frame):
        if not self.call_stack:
            return

        func_key, start_time = self.call_stack.pop()

        if func_key not in self.function_stats:
            return

        stats = self.function_stats[func_key]

        elapsed_ms = (time.time() - start_time) * 1000
        stats.total_time_ms += elapsed_ms

        if self.call_stack:
            caller_key = self.call_stack[-1][0]
            edge_key = (caller_key, func_key)
            if edge_key in self.call_edges:
                self.call_edges[edge_key].total_time_ms += elapsed_ms

        stats._active_calls -= 1

        if stats._resource_samples:
            snapshot = stats._resource_samples[-1]
            stats.peak_memory_mb = max(stats.peak_memory_mb, snapshot.memory_mb)

            if stats.avg_cpu_percent == 0.0:
                stats.avg_cpu_percent = sum(s.cpu_percent for s in stats._resource_samples) / len(
                    stats._resource_samples
                )

        stats._resource_samples.clear()

    def _get_function_key(self, frame) -> FunctionKey:
        """Extract function key from frame with class detection (cached)"""
        code = frame.f_code

        cache_key = (code.co_filename, code.co_name, code.co_firstlineno)

        if cache_key in self._func_key_cache:
            return self._func_key_cache[cache_key]

        classname = None

        if "self" in frame.f_locals:
            try:
                obj = frame.f_locals["self"]
                classname = obj.__class__.__name__
            except Exception:
                pass

        elif "cls" in frame.f_locals:
            try:
                cls = frame.f_locals["cls"]
                classname = cls.__name__
            except Exception:
                pass

        func_key = FunctionKey(
            module=frame.f_globals.get("__name__", ""),
            filename=code.co_filename,
            funcname=code.co_name,
            lineno=code.co_firstlineno,
            classname=classname,
        )

        self._func_key_cache[cache_key] = func_key
        return func_key

    def _should_ignore(self, func_key: FunctionKey) -> bool:
        """Check if function should be ignored"""
        if self.config.collapse_stdlib and ("<" in func_key.filename or ">" in func_key.filename):
            return True

        if func_key.module.startswith("pipelinescope."):
            return True

        for ignored in self._ignore_set:
            if ignored in func_key.filename or ignored in func_key.module:
                return True

        return False
