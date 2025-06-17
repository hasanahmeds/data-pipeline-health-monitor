"""Resource monitoring for CPU and GPU usage"""

import warnings

import GPUtil
import psutil

from .stats import ResourceSnapshot

warnings.filterwarnings(action="ignore", category=DeprecationWarning)


class ResourceMonitor:
    """Monitor CPU and GPU usage"""

    def __init__(self, enable_cpu: bool = True, enable_gpu: bool = True):
        self.enable_cpu = enable_cpu
        self.enable_gpu = enable_gpu
        self.gpu_available = False
        self._gpu_devices = []

        if enable_cpu:
            try:
                self.process = psutil.Process()
            except Exception:
                self.enable_cpu = False

        if enable_gpu:
            try:
                self._gpu_devices = GPUtil.getGPUs()
                self.gpu_available = len(self._gpu_devices) > 0
            except Exception:
                self.gpu_available = False

    def snapshot(self) -> ResourceSnapshot:
        """Capture current resource usage"""
        cpu_percent = 0.0
        memory_mb = 0.0
        gpu_util = []
        gpu_mem = []
