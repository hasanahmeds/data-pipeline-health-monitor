"""Data structures for profiling statistics"""

import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional

warnings.filterwarnings(action="ignore", category=DeprecationWarning)

_STDLIB_MODULES = frozenset(
    [
        "random",
        "threading",
        "json",
        "csv",
        "os",
        "sys",
        "time",
        "datetime",
        "collections",
        "re",
        "math",
        "itertools",
        "functools",
        "io",
        "pathlib",
        "logging",
        "argparse",
        "subprocess",
        "multiprocessing",
        "queue",
        "heapq",
        "bisect",
        "array",
        "copy",
        "pickle",
        "shelve",
        "sqlite3",
        "zlib",
        "gzip",
        "bz2",
        "zipfile",
        "tarfile",
        "hashlib",
        "hmac",
        "secrets",
        "uuid",
        "struct",
        "codecs",
        "base64",
        "binascii",
    ]
)


_STDLIB_INDICATORS = frozenset(
    [
        "/lib/python",
        "\\lib\\python",
        "site-packages",
    ]
)


@dataclass
class FunctionKey:
    """Unique identifier for a function"""

    module: str
    filename: str
    funcname: str
    lineno: int
    classname: Optional[str] = None

    def __hash__(self):
        return hash((self.module, self.filename, self.funcname, self.lineno, self.classname))

    def __eq__(self, other):
        if not isinstance(other, FunctionKey):
            return False
        return (self.module, self.filename, self.funcname, self.lineno, self.classname) == (
            other.module,
            other.filename,
            other.funcname,
            other.lineno,
            other.classname,
        )

    def __post_init__(self):
        self._is_stdlib = self._check_stdlib()

        if self.filename:
            self._stage = self.filename.rsplit(".", 1)[0].rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        else:
            self._stage = self.module or "unknown"

        if self._is_stdlib:
            module_name = self.module.split(".")[-1] if self.module else "unknown"
            self._display_name = f"{module_name}.{self.funcname}"
        else:
            if self.classname:
                self._display_name = f"{self._stage}.{self.classname}.{self.funcname}"
            else:
                self._display_name = f"{self._stage}.{self.funcname}"

    def _check_stdlib(self) -> bool:
        """Check if function is from stdlib (extracted for clarity)"""
        if "<" in self.filename or ">" in self.filename:
            return True

        module_base = self.module.split(".")[0] if self.module else ""
        if module_base in _STDLIB_MODULES:
            return True

        for indicator in _STDLIB_INDICATORS:
            if indicator in self.filename:
                return True

        return False

    @property
    def is_stdlib(self) -> bool:
        return self._is_stdlib

    @property
    def stage(self) -> str:
        return self._stage

    @property
    def display_name(self) -> str:
        return self._display_name


@dataclass
class ResourceSnapshot:
    """CPU/GPU metrics at a point in time"""

    cpu_percent: float
    memory_mb: float
    gpu_utilization: List[float] = field(default_factory=list)
    gpu_memory_mb: List[float] = field(default_factory=list)


@dataclass
class FunctionStats:
    """Statistics for a single function"""

    key: FunctionKey
    call_count: int = 0
    total_time_ms: float = 0.0
    self_time_ms: float = 0.0
    first_call_time: Optional[float] = None

    avg_cpu_percent: float = 0.0
    peak_memory_mb: float = 0.0
    avg_gpu_utilization: List[float] = field(default_factory=list)
    peak_gpu_memory_mb: List[float] = field(default_factory=list)

    _active_calls: int = 0
    _sample_counter: int = 0
    _resource_samples: List[ResourceSnapshot] = field(default_factory=list)

    @property
    def avg_time_ms(self) -> float:
        """Average time per call"""
        return self.total_time_ms / self.call_count if self.call_count > 0 else 0.0


@dataclass
class CallEdge:
    """Edge between caller and callee"""

    caller: FunctionKey
    callee: FunctionKey
    call_count: int = 0
    total_time_ms: float = 0.0

    @property
    def avg_time_ms(self) -> float:
        """Average time per call"""
        return self.total_time_ms / self.call_count if self.call_count > 0 else 0.0


@dataclass
class ProfilingResult:
    """Complete profiling results"""

    function_stats: Dict[FunctionKey, FunctionStats]
    call_edges: Dict[tuple, CallEdge]
    total_runtime_ms: float
    start_timestamp: float
    end_timestamp: float

    def get_total_function_time(self) -> float:
        """Sum of all function times (may exceed total_runtime_ms due to parallel calls)"""
        return sum(stats.total_time_ms for stats in self.function_stats.values())
