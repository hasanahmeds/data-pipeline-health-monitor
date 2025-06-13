"""Configuration management for pipelinescope"""

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

warnings.filterwarnings(action="ignore", category=DeprecationWarning)
warnings.filterwarnings(action="ignore", category=UserWarning, module="pipelinescope")


@dataclass
class PipelineScopeConfig:
    """Configuration for pipelinescope profiling"""

    sample_size: int = 100
    expected_size: int = 1_000_000

    output_dir: str = ".pipelinescope_output"

    enable_dashboard: bool = True
    dashboard_title: str = "PipelineScope"

    min_time_threshold_ms: float = 1.0
    min_time_percentage: float = 0.5

    ignore_modules: List[str] = field(
        default_factory=lambda: ["venv", "site-packages", ".venv", "env"]
    )
    collapse_stdlib: bool = True

    enable_cpu_monitoring: bool = True
    enable_gpu_monitoring: bool = True

    enable_console_logging: bool = False
    log_file: str = "pipelinescope.log"
    log_level: str = "INFO"

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "PipelineScopeConfig":
        """Load config from YAML or use defaults"""
        if config_path is None:
            config_path = cls._discover_config()

        if config_path and config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f) or {}
                config = cls(**data)
                errors = config.validate()
                if errors:
                    import warnings as warn_module

                    for error in errors:
                        warn_module.warn(f"Config validation: {error}", stacklevel=2)
                return config
            except Exception as e:
                import warnings as warn_module

                warn_module.warn(f"Failed to load config {config_path}: {e}", stacklevel=2)

        return cls()

    @staticmethod
    def _discover_config() -> Optional[Path]:
        """Search for .pipelinescope.yaml in current and parent directories"""
        current = Path.cwd()
        for _ in range(6):
            config_file = current / ".pipelinescope.yaml"
            if config_file.exists():
                return config_file
            if current.parent == current:
                break
            current = current.parent
        return None

    def create_default_config(self, path: Path) -> None:
        """Create default config file"""
        if path.exists():
            return

        config_dict = {
            "sample_size": self.sample_size,
            "expected_size": self.expected_size,
            "output_dir": self.output_dir,
            "enable_dashboard": self.enable_dashboard,
            "dashboard_title": self.dashboard_title,
            "min_time_threshold_ms": self.min_time_threshold_ms,
            "min_time_percentage": self.min_time_percentage,
            "ignore_modules": self.ignore_modules,
            "collapse_stdlib": self.collapse_stdlib,
            "enable_cpu_monitoring": self.enable_cpu_monitoring,
            "enable_gpu_monitoring": self.enable_gpu_monitoring,
            "enable_console_logging": self.enable_console_logging,
            "log_file": self.log_file,
            "log_level": self.log_level,
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if self.sample_size <= 0:
            errors.append("sample_size must be > 0")

        if self.expected_size <= 0:
            errors.append("expected_size must be > 0")

        if self.min_time_threshold_ms < 0:
            errors.append("min_time_threshold_ms must be >= 0")

        if not (0 <= self.min_time_percentage <= 100):
            errors.append("min_time_percentage must be between 0 and 100")

        return errors
