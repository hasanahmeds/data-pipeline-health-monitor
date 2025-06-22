from pathlib import Path

import yaml

from pipelinescope.core.config import PipelineScopeConfig


class TestConfigDefaults:
    def test_default_config_creation(self):
        """Test default configuration values"""
        config = PipelineScopeConfig()
        assert config.sample_size == 100
        assert config.expected_size == 1_000_000
        assert config.output_dir == ".pipelinescope_output"
        assert config.enable_dashboard is True
        assert config.collapse_stdlib is True

    def test_default_ignore_modules(self):
        """Test default ignored modules list"""
        config = PipelineScopeConfig()
        assert "venv" in config.ignore_modules
        assert "site-packages" in config.ignore_modules
        assert ".venv" in config.ignore_modules


class TestConfigLoading:
    def test_load_from_yaml_file(self, tmp_path):
        """Test loading config from YAML file"""
        config_file = tmp_path / ".pipelinescope.yaml"
        config_data = {
            "sample_size": 500,
            "expected_size": 5_000_000,
            "output_dir": "custom_output",
            "enable_dashboard": False,
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = PipelineScopeConfig.load(config_file)
        assert config.sample_size == 500
