"""Reporting module for generating static HTML reports"""

from .analyzer import aggregate_by_module, extract_hotspots, get_all_functions
from .generator import generate_static_report

__all__ = [
    "generate_static_report",
    "extract_hotspots",
    "aggregate_by_module",
    "get_all_functions",
]
