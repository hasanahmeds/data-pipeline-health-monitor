from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_psutil(monkeypatch):
    """Mock psutil.Process for CPU/memory monitoring"""
    mock_process = MagicMock()
    mock_process.cpu_percent.return_value = 25.5
    mock_process.memory_info.return_value = MagicMock(rss=512 * 1024 * 1024)

    monkeypatch.setattr("pipelinescope.core.resource_monitor.psutil.Process", lambda: mock_process)
    return mock_process


@pytest.fixture
def mock_gputil(monkeypatch):
    """Mock GPUtil for GPU monitoring"""
    mock_gpu = MagicMock()
    mock_gpu.load = 0.5
    mock_gpu.memoryUsed = 4096

    monkeypatch.setattr("pipelinescope.core.resource_monitor.GPUtil.getGPUs", lambda: [mock_gpu])
    return [mock_gpu]


@pytest.fixture
def reset_global_profiler():
    """Reset global _profiler singleton"""
    import pipelinescope.core.entrypoint as ep_module
    from pipelinescope.core.entrypoint import PipelineProfiler

    original = ep_module._profiler
    ep_module._profiler = PipelineProfiler()
    yield ep_module._profiler
    ep_module._profiler = original


@pytest.fixture
def tmp_pipelinescope(tmp_path):
    """Temp directory for PipelineScope output"""
    output_dir = tmp_path / ".pipelinescope_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def tmp_config_file(tmp_path):
    """Temp directory for config files"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir
