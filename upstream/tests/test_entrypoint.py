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
