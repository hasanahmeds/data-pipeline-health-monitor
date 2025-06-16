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
