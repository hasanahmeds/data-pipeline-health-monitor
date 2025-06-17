"""Entry point for PipelineScope profiling"""

import atexit
import time
import warnings
from pathlib import Path
from typing import Optional

from ..data import serialize_profiling_data
from ..reporting import generate_static_report
from ..utils.logger import get_logger, setup_logging
from .config import PipelineScopeConfig
from .extrapolation import extrapolate
from .profiler import Profiler

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


class PipelineProfiler:
    """Main entry point for pipeline profiling"""

    def __init__(self):
        self.config: Optional[PipelineScopeConfig] = None
        self.profiler: Optional[Profiler] = None
        self.active = False
        self.logger = None

    def start(self, config_path: Optional[Path] = None):
        """
        Start profiling the pipeline.

        Args:
            config_path: Optional path to config file. If None, will auto-discover.
        """
        if self.active:
            return

        self.config = PipelineScopeConfig.load(config_path)

        setup_logging(
            output_dir=self.config.output_dir,
            log_file=self.config.log_file,
            enable_console=self.config.enable_console_logging,
            log_level=self.config.log_level,
        )

        self.logger = get_logger()
        self.logger.info("PipelineScope profiling started")
        self.logger.info(f"Configuration loaded from: {config_path or 'defaults'}")

        if config_path is None and self.config is not None:
            default_config_path = Path.cwd() / ".pipelinescope.yaml"
            self.config.create_default_config(default_config_path)

        self.profiler = Profiler(self.config)

        self.profiler.start()
        self.active = True

        if not hasattr(self, "_atexit_registered"):
            atexit.register(self._finalize)
            self._atexit_registered = True

    def stop(self):
        """Stop profiling and generate outputs"""
        if not self.active or not self.profiler:
            return

        self._finalize()

    def _finalize(self):
        """Generate all outputs"""
        if not self.active or not self.profiler:
            return

        self.active = False

        if not self.logger:
            self.logger = get_logger()

        profiling_result = self.profiler.stop()

        if not profiling_result or not profiling_result.function_stats:
            self.logger.warning("No profiling data collected")
            return

    def _finalize(self):
        """Generate all outputs"""
        if not self.active or not self.profiler or not self.config:
            return

        self.active = False

        if not self.logger:
            self.logger = get_logger()

        try:
            profiling_result = self.profiler.stop()

            if not profiling_result or not profiling_result.function_stats:
                self.logger.warning("No profiling data collected")
                return

            extrapolated_stats = extrapolate(profiling_result, self.config)

            self.logger.info(f"Tracked {len(profiling_result.function_stats)} functions")
            self.logger.info(
                f"Extrapolating from {self.config.sample_size} to {self.config.expected_size}"
            )

            timestamp = int(time.time())
            output_dir = Path(self.config.output_dir) / f"run_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)

            json_path = output_dir / "profile_data.json"
            serialize_profiling_data(profiling_result, extrapolated_stats, json_path)

            if self.config.enable_dashboard:
                html_path = output_dir / "summary.html"
                generate_static_report(profiling_result, extrapolated_stats, self.config, html_path)
                self.logger.info(f"Report generated: {html_path}")
                self.logger.info(f"JSON data saved: {json_path}")
                self.logger.info("PipelineScope profiling complete")
        finally:
            self.profiler = None
            self.config = None


_profiler = PipelineProfiler()


def start(config_path: Optional[Path] = None):
    """
    Start profiling the pipeline.

    Usage:
        from pipelinescope import profile_pipeline

        if __name__ == "__main__":
            profile_pipeline.start()
            main()

    Args:
        config_path: Optional path to config file
    """
    _profiler.start(config_path)


def stop():
    """
    Manually stop profiling and generate outputs.
    Usually not needed as profiling stops automatically on exit.
    """
    _profiler.stop()
