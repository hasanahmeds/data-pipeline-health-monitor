"""HTML report generator using Jinja2"""

import time
import warnings
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader

from ..core.config import PipelineScopeConfig
from ..core.extrapolation import ExtrapolatedStats
from ..core.stats import FunctionKey, ProfilingResult
from ..prompts.llm_optimize import get_optimization_prompt
from .analyzer import aggregate_by_module, extract_hotspots, get_all_functions

warnings.filterwarnings(action="ignore", category=DeprecationWarning)

_CACHED_OPTIMIZATION_PROMPT = None


def _get_cached_optimization_prompt() -> str:
    """Get cached LLM optimization prompt"""
    global _CACHED_OPTIMIZATION_PROMPT
    if _CACHED_OPTIMIZATION_PROMPT is None:
        _CACHED_OPTIMIZATION_PROMPT = get_optimization_prompt()
    return _CACHED_OPTIMIZATION_PROMPT


def format_time_human(ms):
    """Convert milliseconds to human-readable time with optional days."""
    if ms < 1000:
        return f"{int(ms)}ms"

    total_seconds = int(ms / 1000)
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []

    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def generate_static_report(
    profiling_result: ProfilingResult,
    extrapolated_stats: Dict[FunctionKey, ExtrapolatedStats],
    config: PipelineScopeConfig,
    output_path: Path,
) -> None:
    """
    Generate static HTML report.

    Args:
        profiling_result: Profiling results
        extrapolated_stats: Extrapolated statistics
        config: Configuration
        output_path: Path to write HTML file
    """
    top_hotspots = extract_hotspots(profiling_result, extrapolated_stats, top_n=5)
    module_aggregates = aggregate_by_module(profiling_result, extrapolated_stats)
    all_functions = get_all_functions(profiling_result, extrapolated_stats)

    top_modules = module_aggregates[:5]

    _ts = time.time()
    _ts_int = int(_ts)
    _ts_localtime = time.localtime(_ts)

    context = {
        "title": config.dashboard_title,
        "timestamp": _ts_int,
        "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S", _ts_localtime),
        "total_runtime_ms": round(profiling_result.total_runtime_ms, 2),
        "total_runtime_sec": round(profiling_result.total_runtime_ms / 1000, 2),
        "total_functions": len(profiling_result.function_stats),
        "sample_size": config.sample_size,
        "expected_size": config.expected_size,
        "scale_factor": config.expected_size / config.sample_size if config.sample_size > 0 else 1,
        "top_hotspots": [h.to_dict() for h in top_hotspots],
        "top_modules": [m.to_dict() for m in top_modules],
        "all_modules": [m.to_dict() for m in module_aggregates],
        "all_functions": [f.to_dict() for f in all_functions],
        "has_gpu_data": bool(
            all_functions
            and (all_functions[0].avg_gpu_utilization or all_functions[0].peak_gpu_memory_mb)
        ),
        "llm_prompt": _get_cached_optimization_prompt(),
        "min_time_threshold_ms": config.min_time_threshold_ms,
        "min_time_percentage": config.min_time_percentage,
    }

    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    env.filters["format_time"] = format_time_human

    template = env.get_template("summary.html")

    html_content = template.render(**context)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
