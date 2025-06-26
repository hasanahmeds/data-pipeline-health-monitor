import json
import time

import yaml

from pipelinescope.core.entrypoint import PipelineProfiler, start, stop


def dummy_func():
    return 42


class TestPipelineProfilerInit:
    def test_profiler_init(self, reset_global_profiler):
        """Test PipelineProfiler initialization"""
        profiler = PipelineProfiler()
        assert profiler.active is False
        assert profiler.config is None
        assert profiler.profiler is None


class TestPipelineProfilerStartStop:
    def test_profiler_start_stop(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler start and stop lifecycle"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        config_path = tmp_path / ".pipelinescope.yaml"

        profiler.start(config_path)
        assert profiler.active is True
        assert profiler.config is not None

        dummy_func()

        profiler.stop()
        assert profiler.active is False


class TestPipelineProfilerOutputGeneration:
    def test_profiler_generates_json_output(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler generates JSON output file"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        config_path = tmp_path / ".pipelinescope.yaml"

        profiler.start(config_path)
        dummy_func()
        profiler.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        assert output_dir.exists()

        run_dirs = list(output_dir.glob("run_*"))
        assert len(run_dirs) > 0

        json_file = run_dirs[0] / "profile_data.json"
        assert json_file.exists()

    def test_profiler_json_content_valid(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test generated JSON has valid structure"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        config_path = tmp_path / ".pipelinescope.yaml"

        profiler.start(config_path)
        dummy_func()
        dummy_func()
        profiler.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        run_dirs = list(output_dir.glob("run_*"))
        json_file = run_dirs[0] / "profile_data.json"

        with open(json_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "functions" in data
        assert "call_edges" in data
        assert data["metadata"]["total_functions"] > 0


class TestPipelineProfilerConfigCreation:
    def test_profiler_creates_default_config(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler creates default config file"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        dummy_func()
        profiler.stop()

        config_file = tmp_path / ".pipelinescope.yaml"
        assert config_file.exists()


class TestGlobalProfilerFunctions:
    def test_global_start_function(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test global start() function"""
        monkeypatch.chdir(tmp_path)

        start()
        dummy_func()
        stop()

        output_dir = tmp_path / ".pipelinescope_output"
        assert output_dir.exists()


class TestPipelineProfilerIdempotentStart:
    def test_start_twice_safe(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test calling start twice is safe"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        profiler.start()
        dummy_func()
        profiler.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        assert output_dir.exists()


class TestPipelineProfilerFinalize:
    def test_finalize_called_on_stop(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test _finalize is called when stop is called"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        dummy_func()
        profiler.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        run_dirs = list(output_dir.glob("run_*"))
        assert len(run_dirs) > 0


class TestPipelineProfilerLogging:
    def test_profiler_initializes_logger(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler initializes logging"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        assert profiler.logger is not None
        dummy_func()
        profiler.stop()


class TestPipelineProfilerCustomConfig:
    def test_profiler_with_custom_config(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler with custom config file"""

        monkeypatch.chdir(tmp_path)

        config_path = tmp_path / "custom.yaml"
        config_data = {"sample_size": 50, "expected_size": 5000, "output_dir": "custom_output"}
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        profiler = PipelineProfiler()
        profiler.start(config_path)
        assert profiler.config.sample_size == 50
        dummy_func()
        profiler.stop()


class TestPipelineProfilerNoData:
    def test_profiler_handles_no_profiling_data(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler handles case with no tracked functions"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        profiler.stop()


class TestPipelineProfilerMultipleRuns:
    def test_profiler_creates_timestamped_runs(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler creates separate directories for each run"""

        monkeypatch.chdir(tmp_path)

        profiler1 = PipelineProfiler()
        profiler1.start()
        dummy_func()
        profiler1.stop()

        time.sleep(0.01)

        profiler2 = PipelineProfiler()
        profiler2.start()
        dummy_func()
        profiler2.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        run_dirs = sorted(output_dir.glob("run_*"))

        assert len(run_dirs) >= 1


class TestPipelineProfilerHtmlGeneration:
    def test_profiler_generates_html(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler generates HTML report"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()
        dummy_func()
        profiler.stop()

        output_dir = tmp_path / ".pipelinescope_output"
        run_dirs = list(output_dir.glob("run_*"))
        assert len(run_dirs) > 0

        html_file = run_dirs[0] / "summary.html"
        assert html_file.exists()
        assert html_file.stat().st_size > 0


class TestPipelineProfilerAtexit:
    def test_profiler_registers_atexit(self, reset_global_profiler, tmp_path, monkeypatch):
        """Test profiler registers atexit handler"""
        monkeypatch.chdir(tmp_path)

        profiler = PipelineProfiler()
        profiler.start()

        assert hasattr(profiler, "_atexit_registered")

        dummy_func()
        profiler.stop()
