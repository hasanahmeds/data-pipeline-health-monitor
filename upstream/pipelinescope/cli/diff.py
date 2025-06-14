"""Comparison CLI tool for comparing multiple profiling runs"""

import argparse
import json
import time
import warnings
from pathlib import Path
from typing import Dict, List, Tuple

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


class FunctionComparison:
    """Comparison of a function across runs"""

    def __init__(self, signature: str):
        self.signature = signature
        self.runs: Dict[str, dict] = {}

    def add_run(self, run_id: str, metrics: dict):
        """Add metrics from a run"""
        self.runs[run_id] = metrics

    def get_change(self, run1_id: str, run2_id: str) -> Tuple[str, float]:
        """
        Get change status between two runs.

        Returns:
            Tuple of (status, percent_change)
            status: 'improved', 'regressed', 'new', 'removed', 'stable'
        """
        run1_exists = run1_id in self.runs
        run2_exists = run2_id in self.runs

        if not run1_exists and run2_exists:
            return ("new", 0.0)
        elif run1_exists and not run2_exists:
            return ("removed", 0.0)
        elif not run1_exists and not run2_exists:
            return ("stable", 0.0)

        time1 = self.runs[run1_id].get("projected_time_ms", 0)
        time2 = self.runs[run2_id].get("projected_time_ms", 0)

        if time1 == 0:
            return ("stable", 0.0)

        percent_change = ((time2 - time1) / time1) * 100

        if percent_change < -10:
            return ("improved", percent_change)
        elif percent_change > 10:
            return ("regressed", percent_change)
        else:
            return ("stable", percent_change)


def load_run_data(run_dir: Path) -> Tuple[str, Dict[str, dict]]:
    """
    Load profiling data from a run directory.

    Args:
        run_dir: Path to run directory (e.g., run_1234567890)

    Returns:
        Tuple of (run_id, functions_dict)
        functions_dict maps signature -> metrics
    """
    json_path = run_dir / "profile_data.json"

    if not json_path.exists():
        raise FileNotFoundError(f"profile_data.json not found in {run_dir}")

    with open(json_path, "r") as f:
        data = json.load(f)

    run_id = run_dir.name

    functions = {}
    for func in data.get("functions", []):
