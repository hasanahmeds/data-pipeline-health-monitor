from pipelinescope.core.stats import (
    CallEdge,
    FunctionKey,
    FunctionStats,
    ProfilingResult,
    ResourceSnapshot,
)


class TestFunctionKey:
    def test_function_key_basic(self):
        """Test basic FunctionKey creation"""
        key = FunctionKey(
            module="data_loader",
            filename="/home/user/data_loader.py",
            funcname="load_csv",
            lineno=42,
        )
        assert key.module == "data_loader"
        assert key.funcname == "load_csv"
        assert key.lineno == 42

    def test_function_key_with_class(self):
        """Test FunctionKey with class name"""
        key = FunctionKey(
            module="processor",
            filename="/home/user/processor.py",
            funcname="process",
            lineno=100,
            classname="DataProcessor",
        )
        assert key.classname == "DataProcessor"
        assert "DataProcessor" in key.display_name
        assert "process" in key.display_name

    def test_function_key_equality(self):
        """Test FunctionKey equality"""
        key1 = FunctionKey(module="module1", filename="file.py", funcname="func", lineno=10)
        key2 = FunctionKey(module="module1", filename="file.py", funcname="func", lineno=10)
        assert key1 == key2

    def test_function_key_hash(self):
        """Test FunctionKey hashability"""
        key1 = FunctionKey(module="module1", filename="file.py", funcname="func", lineno=10)
        key2 = FunctionKey(module="module1", filename="file.py", funcname="func", lineno=10)
        assert hash(key1) == hash(key2)
        d = {key1: "value"}
        assert d[key2] == "value"

    def test_function_key_stdlib_detection(self):
        """Test stdlib function detection"""
        stdlib_key = FunctionKey(
            module="random", filename="<frozen importlib._bootstrap>", funcname="_load", lineno=0
        )
        assert stdlib_key.is_stdlib is True

        user_key = FunctionKey(
            module="mymodule", filename="/home/user/mymodule.py", funcname="my_func", lineno=10
        )
        assert user_key.is_stdlib is False

    def test_function_key_display_name_without_class(self):
        """Test display_name for non-method functions"""
        key = FunctionKey(
            module="processor",
            filename="/home/user/processor.py",
            funcname="transform_data",
            lineno=50,
        )
        assert "processor" in key.display_name
        assert "transform_data" in key.display_name

    def test_function_key_display_name_with_class(self):
        """Test display_name for methods"""
        key = FunctionKey(
            module="processor",
            filename="/home/user/processor.py",
            funcname="process",
            lineno=60,
            classname="Pipeline",
        )
        assert "Pipeline" in key.display_name
        assert "process" in key.display_name


class TestFunctionStats:
    def test_function_stats_basic(self):
        """Test basic FunctionStats"""
        key = FunctionKey(module="module", filename="file.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=10, total_time_ms=100.0)
        assert stats.call_count == 10
        assert stats.total_time_ms == 100.0
        assert stats.avg_time_ms == 10.0

    def test_function_stats_with_resources(self):
        """Test FunctionStats with resource metrics"""
        key = FunctionKey(module="module", filename="file.py", funcname="func", lineno=1)
        stats = FunctionStats(
            key=key, call_count=5, total_time_ms=50.0, avg_cpu_percent=25.5, peak_memory_mb=256.0
        )
        assert stats.avg_cpu_percent == 25.5
        assert stats.peak_memory_mb == 256.0

    def test_function_stats_zero_calls(self):
        """Test FunctionStats with zero calls"""
        key = FunctionKey(module="module", filename="file.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=0)
        assert stats.avg_time_ms == 0.0


class TestResourceSnapshot:
    def test_resource_snapshot_cpu_only(self):
        """Test ResourceSnapshot with CPU metrics"""
        snapshot = ResourceSnapshot(cpu_percent=45.2, memory_mb=512.5)
        assert snapshot.cpu_percent == 45.2
        assert snapshot.memory_mb == 512.5

    def test_resource_snapshot_with_gpu(self):
        """Test ResourceSnapshot with GPU metrics"""
        snapshot = ResourceSnapshot(
            cpu_percent=30.0,
            memory_mb=256.0,
            gpu_utilization=[0.75, 0.50],
            gpu_memory_mb=[4096, 2048],
        )
        assert len(snapshot.gpu_utilization) == 2
        assert snapshot.gpu_utilization[0] == 0.75
        assert len(snapshot.gpu_memory_mb) == 2


class TestCallEdge:
    def test_call_edge_basic(self):
        """Test CallEdge creation"""
        caller = FunctionKey(module="m1", filename="f1.py", funcname="func_a", lineno=1)
        callee = FunctionKey(module="m2", filename="f2.py", funcname="func_b", lineno=2)
        edge = CallEdge(caller=caller, callee=callee, call_count=5, total_time_ms=50.0)
        assert edge.call_count == 5
        assert edge.avg_time_ms == 10.0


class TestProfilingResult:
    def test_profiling_result_basic(self):
        """Test ProfilingResult creation"""
        key1 = FunctionKey(module="m", filename="f.py", funcname="f1", lineno=1)
        key2 = FunctionKey(module="m", filename="f.py", funcname="f2", lineno=2)

        stats1 = FunctionStats(key=key1, call_count=10, total_time_ms=100.0)
        stats2 = FunctionStats(key=key2, call_count=5, total_time_ms=50.0)

        result = ProfilingResult(
            function_stats={key1: stats1, key2: stats2},
            call_edges={},
            total_runtime_ms=150.0,
            start_timestamp=1000.0,
            end_timestamp=1000.15,
        )
        assert len(result.function_stats) == 2
        assert result.total_runtime_ms == 150.0

    def test_profiling_result_get_total_function_time(self):
        """Test total function time calculation"""
        key1 = FunctionKey(module="m", filename="f.py", funcname="f1", lineno=1)
        key2 = FunctionKey(module="m", filename="f.py", funcname="f2", lineno=2)

        stats1 = FunctionStats(key=key1, total_time_ms=100.0)
        stats2 = FunctionStats(key=key2, total_time_ms=50.0)

        result = ProfilingResult(
            function_stats={key1: stats1, key2: stats2},
            call_edges={},
            total_runtime_ms=150.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        assert result.get_total_function_time() == 150.0


class TestFunctionKeyStageProperty:
    def test_stage_extraction(self):
        """Test stage extraction from filename"""
        key = FunctionKey(
            module="mypackage.submodule",
            filename="/path/to/data_loader.py",
            funcname="load",
            lineno=10,
        )
        assert key.stage == "data_loader"

    def test_stage_without_extension(self):
        """Test stage with path separators"""
        key = FunctionKey(module="m", filename="processor.py", funcname="process", lineno=1)
        assert key.stage == "processor"
