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
        module = func.get("module", "unknown")
        classname = func.get("classname")
        funcname = func.get("funcname", "unknown")

        if classname:
            signature = f"{module}.{classname}.{funcname}"
        else:
            signature = f"{module}.{funcname}"

        functions[signature] = func

    return run_id, functions


def compare_runs(output_dir: Path, run_ids: List[str] = None) -> str:
    """
    Compare multiple profiling runs.

    Args:
        output_dir: Output directory containing run folders
        run_ids: List of run IDs to compare (None = all runs)

    Returns:
        HTML content for comparison report
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    run_dirs = sorted(
        [d for d in output_path.iterdir() if d.is_dir() and d.name.startswith("run_")]
    )

    if not run_dirs:
        raise ValueError(f"No run directories found in {output_dir}")

    if run_ids:
        run_dirs = [d for d in run_dirs if d.name in run_ids]

    if len(run_dirs) < 2:
        raise ValueError("Need at least 2 runs to compare")

    all_runs = {}
    for run_dir in run_dirs:
        run_id, functions = load_run_data(run_dir)
        all_runs[run_id] = functions

    comparisons = {}
    for run_id, functions in all_runs.items():
        for signature, metrics in functions.items():
            if signature not in comparisons:
                comparisons[signature] = FunctionComparison(signature)
            comparisons[signature].add_run(run_id, metrics)

    run_ids_sorted = sorted(all_runs.keys())

    if len(run_ids_sorted) >= 2:
        run1_id = run_ids_sorted[-2]
        run2_id = run_ids_sorted[-1]
    else:
        run1_id = run_ids_sorted[0]
        run2_id = run_ids_sorted[0]

    improved = []
    regressed = []
    new_funcs = []
    removed_funcs = []

    for signature, comp in comparisons.items():
        status, percent_change = comp.get_change(run1_id, run2_id)

        if status == "improved":
            improved.append((signature, percent_change, comp.runs[run2_id]))
        elif status == "regressed":
            regressed.append((signature, percent_change, comp.runs[run2_id]))
        elif status == "new":
            new_funcs.append((signature, comp.runs[run2_id]))
        elif status == "removed":
            removed_funcs.append((signature, comp.runs[run1_id]))

    improved.sort(key=lambda x: x[1])
    regressed.sort(key=lambda x: -x[1])
    html = generate_comparison_html(run1_id, run2_id, improved, regressed, new_funcs, removed_funcs)

    return html


def generate_comparison_html(
    run1_id: str,
    run2_id: str,
    improved: List[Tuple],
    regressed: List[Tuple],
    new_funcs: List[Tuple],
    removed_funcs: List[Tuple],
) -> str:
    """Generate HTML for comparison report"""

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    parts = [
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PipelineScope Comparison Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            color: #212529;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .meta {{ color: #6c757d; font-size: 14px; }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        .improved {{ border-left: 4px solid #28a745; }}
        .regressed {{ border-left: 4px solid #dc3545; }}
        .new {{ border-left: 4px solid #007bff; }}
        .removed {{ border-left: 4px solid #6c757d; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
        }}
        .badge {{
