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
        assert config.expected_size == 5_000_000
        assert config.output_dir == "custom_output"
        assert config.enable_dashboard is False

    def test_load_nonexistent_file_returns_defaults(self):
        """Test loading from nonexistent file returns defaults"""
        config = PipelineScopeConfig.load(Path("/nonexistent/path/.pipelinescope.yaml"))
        assert config.sample_size == 100
        assert config.expected_size == 1_000_000

    def test_load_with_none_uses_discovery(self, tmp_path, monkeypatch):
        """Test load(None) uses discovery"""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".pipelinescope.yaml"
        config_data = {"sample_size": 250}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = PipelineScopeConfig.load(None)
        assert config.sample_size == 250

    def test_load_invalid_yaml_returns_defaults(self, tmp_path, recwarn):
        """Test invalid YAML returns defaults with warning"""
        config_file = tmp_path / ".pipelinescope.yaml"
        config_file.write_text("invalid: yaml: content: [")
        config = PipelineScopeConfig.load(config_file)
        assert any(w.category is UserWarning for w in recwarn)
        assert config.sample_size == 100


class TestConfigValidation:
    def test_validate_positive_sample_size(self):
        """Test validation fails for non-positive sample_size"""
        config = PipelineScopeConfig(sample_size=0)
        errors = config.validate()
        assert len(errors) > 0
        assert any("sample_size" in e for e in errors)

    def test_validate_positive_expected_size(self):
        """Test validation fails for non-positive expected_size"""
        config = PipelineScopeConfig(expected_size=-1)
        errors = config.validate()
        assert any("expected_size" in e for e in errors)

    def test_validate_min_time_threshold(self):
        """Test validation for min_time_threshold_ms"""
        config = PipelineScopeConfig(min_time_threshold_ms=-1)
        errors = config.validate()
        assert any("min_time_threshold_ms" in e for e in errors)

    def test_validate_min_time_percentage(self):
        """Test validation for min_time_percentage"""
        config = PipelineScopeConfig(min_time_percentage=101)
        errors = config.validate()
        assert any("min_time_percentage" in e for e in errors)

    def test_valid_config_no_errors(self):
        """Test valid config produces no errors"""
        config = PipelineScopeConfig()
        errors = config.validate()
        assert len(errors) == 0


class TestConfigDiscovery:
    def test_discover_config_in_current_dir(self, tmp_path, monkeypatch):
        """Test discovery finds .pipelinescope.yaml in current directory"""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / ".pipelinescope.yaml"
        config_file.write_text("sample_size: 200")

        discovered = PipelineScopeConfig._discover_config()
        assert discovered is not None
        assert discovered.exists()

    def test_discover_config_in_parent_dir(self, tmp_path, monkeypatch):
        """Test discovery finds config in parent directory"""
        config_file = tmp_path / ".pipelinescope.yaml"
        config_file.write_text("sample_size: 200")

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        monkeypatch.chdir(subdir)

        discovered = PipelineScopeConfig._discover_config()
        assert discovered is not None
        assert discovered.name == ".pipelinescope.yaml"

    def test_discover_returns_none_no_config(self, tmp_path, monkeypatch):
        """Test discovery returns None when no config found"""
        monkeypatch.chdir(tmp_path)
        discovered = PipelineScopeConfig._discover_config()
        assert discovered is None


class TestConfigFileCreation:
    def test_create_default_config_file(self, tmp_path):
        """Test creating default config file"""
        config_path = tmp_path / ".pipelinescope.yaml"
        config = PipelineScopeConfig()
        config.create_default_config(config_path)

        assert config_path.exists()
        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data["sample_size"] == 100
        assert data["expected_size"] == 1_000_000

    def test_create_default_config_not_overwrites(self, tmp_path):
        """Test create_default_config doesn't overwrite existing file"""
        config_path = tmp_path / ".pipelinescope.yaml"
        config_path.write_text("sample_size: 999")

        config = PipelineScopeConfig()
        config.create_default_config(config_path)

        with open(config_path) as f:
            data = yaml.safe_load(f)
        assert data["sample_size"] == 999


class TestConfigEdgeCases:
    def test_config_with_custom_ignore_modules(self, tmp_path):
        """Test config with custom ignore modules"""
        config_file = tmp_path / ".pipelinescope.yaml"
        config_data = {"ignore_modules": ["custom_module", "another_module"]}
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = PipelineScopeConfig.load(config_file)
        assert "custom_module" in config.ignore_modules
        assert "another_module" in config.ignore_modules

    def test_config_log_level_options(self):
        """Test various log level options"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            config = PipelineScopeConfig(log_level=level)
            assert config.log_level == level

    def test_config_extrapolation_scaling(self):
        """Test extrapolation scale factor calculation"""
        config = PipelineScopeConfig(sample_size=100, expected_size=10000)
        scale_factor = config.expected_size / config.sample_size
        assert scale_factor == 100
