from pipelinescope.core.resource_monitor import ResourceMonitor


class TestResourceMonitorBasic:
    def test_resource_monitor_init(self, mock_psutil, mock_gputil):
        """Test ResourceMonitor initialization"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=True)
        assert monitor.enable_cpu is True
        assert monitor.enable_gpu is True

    def test_resource_monitor_cpu_snapshot(self, mock_psutil, mock_gputil):
        """Test CPU resource snapshot"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=False)
        snapshot = monitor.snapshot()

        assert snapshot.cpu_percent == 25.5
        assert snapshot.memory_mb == 512.0

    def test_resource_monitor_gpu_snapshot(self, mock_psutil, mock_gputil):
        """Test GPU resource snapshot"""
        monitor = ResourceMonitor(enable_cpu=False, enable_gpu=True)
        snapshot = monitor.snapshot()

        assert len(snapshot.gpu_utilization) == 1
        assert snapshot.gpu_utilization[0] == 50.0
        assert len(snapshot.gpu_memory_mb) == 1
        assert snapshot.gpu_memory_mb[0] == 4096


class TestResourceMonitorCPUOnly:
    def test_cpu_only_monitoring(self, mock_psutil):
        """Test CPU-only monitoring without GPU"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=False)
        snapshot = monitor.snapshot()

        assert snapshot.cpu_percent == 25.5
        assert snapshot.memory_mb == 512.0
        assert len(snapshot.gpu_utilization) == 0
        assert len(snapshot.gpu_memory_mb) == 0


class TestResourceMonitorGPUOnly:
    def test_gpu_only_monitoring(self, mock_gputil):
        """Test GPU-only monitoring without CPU"""
        monitor = ResourceMonitor(enable_cpu=False, enable_gpu=True)
        snapshot = monitor.snapshot()

        assert snapshot.cpu_percent == 0.0
        assert snapshot.memory_mb == 0.0
        assert len(snapshot.gpu_utilization) == 1
        assert snapshot.gpu_utilization[0] == 50.0


class TestResourceMonitorDisabled:
    def test_monitoring_disabled(self):
        """Test with monitoring disabled"""
        monitor = ResourceMonitor(enable_cpu=False, enable_gpu=False)
        snapshot = monitor.snapshot()

        assert snapshot.cpu_percent == 0.0
        assert snapshot.memory_mb == 0.0
        assert len(snapshot.gpu_utilization) == 0
        assert len(snapshot.gpu_memory_mb) == 0


class TestResourceMonitorMultipleSnapshots:
    def test_multiple_snapshots(self, mock_psutil, mock_gputil):
        """Test taking multiple snapshots"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=True)

        snapshot1 = monitor.snapshot()
        snapshot2 = monitor.snapshot()
        snapshot3 = monitor.snapshot()

        assert snapshot1.cpu_percent == snapshot2.cpu_percent
        assert snapshot2.memory_mb == snapshot3.memory_mb

    def test_snapshot_consistency(self, mock_psutil, mock_gputil):
        """Test snapshot values are consistent"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=True)

        snapshots = [monitor.snapshot() for _ in range(5)]

        for snapshot in snapshots:
            assert snapshot.cpu_percent == 25.5


class TestResourceMonitorExceptionHandling:
    def test_monitor_handles_cpu_error(self, monkeypatch):
        """Test monitor handles CPU monitoring error gracefully"""

        def failing_process(*args, **kwargs):
            raise Exception("Process creation failed")

        monkeypatch.setattr("pipelinescope.core.resource_monitor.psutil.Process", failing_process)

        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=False)
        snapshot = monitor.snapshot()
        assert snapshot.cpu_percent == 0.0

    def test_monitor_handles_gpu_error(self, monkeypatch):
        """Test monitor handles GPU monitoring error gracefully"""

        def failing_gpu(*args, **kwargs):
            raise Exception("GPU query failed")

        monkeypatch.setattr("pipelinescope.core.resource_monitor.GPUtil.getGPUs", failing_gpu)

        monitor = ResourceMonitor(enable_cpu=False, enable_gpu=True)
        assert monitor.gpu_available is False
        snapshot = monitor.snapshot()
        assert len(snapshot.gpu_utilization) == 0


class TestResourceMonitorMemoryCalculation:
    def test_memory_conversion(self, mock_psutil):
        """Test memory is converted correctly from bytes to MB"""
        monitor = ResourceMonitor(enable_cpu=True, enable_gpu=False)
        snapshot = monitor.snapshot()

        assert snapshot.memory_mb == 512.0
