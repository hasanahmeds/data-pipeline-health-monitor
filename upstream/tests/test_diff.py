import json

import pytest

from pipelinescope.cli.diff import (
    FunctionComparison,
    compare_runs,
    generate_comparison_html,
    load_run_data,
)


class TestFunctionComparison:
    def test_function_comparison_init(self):
        """Test FunctionComparison initialization"""
        comp = FunctionComparison("module.func")
        assert comp.signature == "module.func"
        assert len(comp.runs) == 0

    def test_function_comparison_add_run(self):
        """Test adding run metrics"""
        comp = FunctionComparison("module.func")
        metrics = {"projected_time_ms": 100.0}
        comp.add_run("run_1", metrics)

        assert "run_1" in comp.runs
        assert comp.runs["run_1"]["projected_time_ms"] == 100.0

    def test_function_comparison_improved(self):
        """Test detecting improved functions"""
        comp = FunctionComparison("module.func")
        comp.add_run("run_1", {"projected_time_ms": 100.0})
        comp.add_run("run_2", {"projected_time_ms": 50.0})

        status, change = comp.get_change("run_1", "run_2")
        assert status == "improved"
        assert change < 0

    def test_function_comparison_regressed(self):
        """Test detecting regressed functions"""
        comp = FunctionComparison("module.func")
        comp.add_run("run_1", {"projected_time_ms": 100.0})
        comp.add_run("run_2", {"projected_time_ms": 150.0})

        status, change = comp.get_change("run_1", "run_2")
        assert status == "regressed"
        assert change > 0

    def test_function_comparison_stable(self):
        """Test detecting stable functions"""
        comp = FunctionComparison("module.func")
        comp.add_run("run_1", {"projected_time_ms": 100.0})
        comp.add_run("run_2", {"projected_time_ms": 105.0})

        status, change = comp.get_change("run_1", "run_2")
        assert status == "stable"

    def test_function_comparison_new(self):
        """Test detecting new functions"""
        comp = FunctionComparison("module.func")
        comp.add_run("run_2", {"projected_time_ms": 100.0})

        status, change = comp.get_change("run_1", "run_2")
        assert status == "new"

    def test_function_comparison_removed(self):
        """Test detecting removed functions"""
        comp = FunctionComparison("module.func")
        comp.add_run("run_1", {"projected_time_ms": 100.0})

        status, change = comp.get_change("run_1", "run_2")
        assert status == "removed"


class TestLoadRunData:
    def test_load_run_data_basic(self, tmp_path):
        """Test loading run data from JSON"""
        run_dir = tmp_path / "run_1234567890"
        run_dir.mkdir()

        data = {
            "functions": [
                {
                    "module": "test",
                    "funcname": "func1",
                    "classname": None,
                    "projected_time_ms": 100.0,
                }
            ]
        }

        json_path = run_dir / "profile_data.json"
        with open(json_path, "w") as f:
            json.dump(data, f, indent=None, separators=(",", ":"))

        run_id, functions = load_run_data(run_dir)
        assert run_id == "run_1234567890"
        assert len(functions) > 0

    def test_load_run_data_with_class(self, tmp_path):
        """Test loading run data with class names"""
        run_dir = tmp_path / "run_1234567890"
        run_dir.mkdir()

        data = {
            "functions": [
                {
                    "module": "test",
                    "funcname": "func1",
                    "classname": "MyClass",
                    "projected_time_ms": 100.0,
                }
            ]
        }

        json_path = run_dir / "profile_data.json"
        with open(json_path, "w") as f:
            json.dump(data, f, indent=None, separators=(",", ":"))

        run_id, functions = load_run_data(run_dir)

        assert "test.MyClass.func1" in functions

    def test_load_run_data_missing_file(self, tmp_path):
        """Test loading from directory without profile_data.json"""
        run_dir = tmp_path / "run_1234567890"
        run_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            load_run_data(run_dir)


class TestCompareRuns:
    def test_compare_runs_basic(self, tmp_path):
        """Test comparing two runs"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        run1_dir = output_dir / "run_1000"
        run1_dir.mkdir()
        data1 = {
            "functions": [
                {
                    "module": "test",
                    "funcname": "func1",
                    "classname": None,
                    "projected_time_ms": 100.0,
                }
            ]
        }
        with open(run1_dir / "profile_data.json", "w") as f:
            json.dump(data1, f, indent=None, separators=(",", ":"))

        run2_dir = output_dir / "run_2000"
        run2_dir.mkdir()
        data2 = {
            "functions": [
                {
                    "module": "test",
                    "funcname": "func1",
