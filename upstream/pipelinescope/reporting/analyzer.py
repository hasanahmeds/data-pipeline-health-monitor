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
