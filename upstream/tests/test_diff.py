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
                    "classname": None,
                    "projected_time_ms": 50.0,
                }
            ]
        }
        with open(run2_dir / "profile_data.json", "w") as f:
            json.dump(data2, f, indent=None, separators=(",", ":"))

        html = compare_runs(output_dir)
        assert isinstance(html, str)
        assert len(html) > 0
        assert "html" in html.lower()

    def test_compare_runs_no_runs_error(self, tmp_path):
        """Test compare_runs with no run directories"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ValueError):
            compare_runs(output_dir)

    def test_compare_runs_single_run_error(self, tmp_path):
        """Test compare_runs with only one run"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        run_dir = output_dir / "run_1000"
        run_dir.mkdir()
        data = {"functions": []}
        with open(run_dir / "profile_data.json", "w") as f:
            json.dump(data, f, indent=None, separators=(",", ":"))

        with pytest.raises(ValueError):
            compare_runs(output_dir)


class TestGenerateComparisonHtml:
    def test_generate_comparison_html_basic(self):
        """Test HTML generation for comparison"""
        improved = [("test.func1", -15.0, {"projected_time_ms": 85.0, "percentage_of_total": 10.0})]
        regressed = []
        new_funcs = []
        removed = []

        html = generate_comparison_html("run_1", "run_2", improved, regressed, new_funcs, removed)

        assert "<html" in html.lower()
        assert "</html>" in html.lower()
        assert "test.func1" in html
        assert "-15" in html

    def test_generate_comparison_html_with_all_types(self):
        """Test HTML generation with all function types"""
        improved = [("test.func1", -15.0, {"projected_time_ms": 85.0, "percentage_of_total": 10.0})]
        regressed = [
            ("test.func2", 20.0, {"projected_time_ms": 120.0, "percentage_of_total": 15.0})
        ]
        new_funcs = [("test.func3", {"projected_time_ms": 50.0, "percentage_of_total": 5.0})]
        removed = [("test.func4", {"projected_time_ms": 75.0})]

        html = generate_comparison_html("run_1", "run_2", improved, regressed, new_funcs, removed)

        assert "test.func1" in html
        assert "test.func2" in html
        assert "test.func3" in html
        assert "test.func4" in html

    def test_generate_comparison_html_empty(self):
        """Test HTML generation with no changes"""
        html = generate_comparison_html("run_1", "run_2", [], [], [], [])

        assert "html" in html.lower()
        assert "run_1" in html
        assert "run_2" in html


class TestComparisonWorkflow:
    def test_full_comparison_workflow(self, tmp_path):
        """Test full workflow: create 2 runs and compare"""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        run1 = output_dir / "run_1000"
        run1.mkdir()
        data1 = {
            "functions": [
                {"module": "m1", "funcname": "f1", "classname": None, "projected_time_ms": 100.0},
                {"module": "m2", "funcname": "f2", "classname": None, "projected_time_ms": 50.0},
            ]
        }
        with open(run1 / "profile_data.json", "w") as f:
            json.dump(data1, f, indent=None, separators=(",", ":"))

        run2 = output_dir / "run_2000"
        run2.mkdir()
        data2 = {
            "functions": [
                {"module": "m1", "funcname": "f1", "classname": None, "projected_time_ms": 80.0},
                {"module": "m2", "funcname": "f2", "classname": None, "projected_time_ms": 60.0},
            ]
        }
        with open(run2 / "profile_data.json", "w") as f:
            json.dump(data2, f, indent=None, separators=(",", ":"))

        html = compare_runs(output_dir)
        assert "run_1000" in html
        assert "run_2000" in html
