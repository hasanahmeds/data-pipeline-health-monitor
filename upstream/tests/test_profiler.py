from pipelinescope.core.config import PipelineScopeConfig
from pipelinescope.core.profiler import Profiler
from pipelinescope.core.stats import FunctionKey


def simple_func():
    """Simple function for profiling"""
    return 42


def func_with_calls():
    """Function that calls another function"""
    simple_func()
    simple_func()
    return "done"


def recursive_helper(n):
    """Helper for recursion test"""
    if n <= 0:
        return 1
    return n * recursive_helper(n - 1)


class TestProfilerBasic:
    def test_profiler_init(self):
        """Test Profiler initialization"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)
        assert profiler.active is False
        assert len(profiler.function_stats) == 0

    def test_profiler_start_stop(self):
        """Test profiler start/stop"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        assert profiler.active is True

        result = profiler.stop()
        assert profiler.active is False
        assert result is not None
        assert isinstance(result.function_stats, dict)

    def test_profiler_tracks_function_call(self):
        """Test profiler tracks function calls"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        simple_func()
        result = profiler.stop()

        assert len(result.function_stats) > 0
        found = False
        for key, stats in result.function_stats.items():
            if key.funcname == "simple_func":
                found = True
                assert stats.call_count >= 1
                break
        assert found

    def test_profiler_tracks_multiple_calls(self):
        """Test profiler tracks multiple calls to same function"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        for _ in range(5):
            simple_func()
        result = profiler.stop()

        for key, stats in result.function_stats.items():
            if key.funcname == "simple_func":
                assert stats.call_count >= 5
                break


class TestProfilerCallStack:
    def test_profiler_tracks_call_edges(self):
        """Test profiler tracks calls between functions"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        func_with_calls()
        result = profiler.stop()

        found_edge = False
        for (caller, callee), edge in result.call_edges.items():
            if callee.funcname == "simple_func" and caller.funcname == "func_with_calls":
                found_edge = True
                assert edge.call_count >= 2
                break
        assert found_edge


class TestProfilerTiming:
    def test_profiler_measures_time(self):
        """Test profiler measures execution time"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        simple_func()
        result = profiler.stop()

        assert result.total_runtime_ms > 0
        assert result.start_timestamp < result.end_timestamp

    def test_profiler_accumulates_time(self):
        """Test profiler accumulates time across calls"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        for _ in range(3):
            simple_func()
        result = profiler.stop()

        for key, stats in result.function_stats.items():
            if key.funcname == "simple_func":
                assert stats.total_time_ms >= 0
                break


class TestProfilerIgnore:
    def test_profiler_ignores_venv(self):
        """Test profiler ignores venv modules"""
        config = PipelineScopeConfig(ignore_modules=["venv"])
        profiler = Profiler(config)

        key = FunctionKey(
            module="venv.test", filename="/venv/lib/python3.9/test.py", funcname="test", lineno=1
        )
        assert profiler._should_ignore(key) is True

    def test_profiler_ignores_pipelinescope(self):
        """Test profiler ignores pipelinescope internals"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        key = FunctionKey(
            module="pipelinescope.core.profiler",
            filename="/path/to/profiler.py",
            funcname="_profile_callback",
            lineno=1,
        )
        assert profiler._should_ignore(key) is True

    def test_profiler_ignores_stdlib(self):
        """Test profiler ignores stdlib with angle brackets"""
        config = PipelineScopeConfig(collapse_stdlib=True)
        profiler = Profiler(config)

        key = FunctionKey(
            module="importlib", filename="<frozen importlib._bootstrap>", funcname="_load", lineno=1
        )
        assert profiler._should_ignore(key) is True


class TestProfilerResourceMonitoring:
    def test_profiler_samples_resources(self, mock_psutil, mock_gputil):
        """Test profiler samples CPU/GPU resources"""
        config = PipelineScopeConfig(enable_cpu_monitoring=True, enable_gpu_monitoring=True)
        profiler = Profiler(config)

        profiler.start()
        for _ in range(200):
            simple_func()
        result = profiler.stop()

        for stats in result.function_stats.values():
            if stats.call_count > 100:
                assert stats.peak_memory_mb >= 0


class TestProfilerFunctionKey:
    def test_profiler_extracts_function_key(self):
        """Test _get_function_key extracts correct info"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        simple_func()
        result = profiler.stop()

        found = False
        for key in result.function_stats.keys():
            if key.funcname == "simple_func":
                assert key.filename.endswith("test_profiler.py")
                assert key.module == "__main__" or "test_profiler" in key.module
                found = True
                break
        assert found

    def test_profiler_detects_class_methods(self):
        """Test _get_function_key detects class methods"""

        class TestClass:
            def method(self):
                return "result"

        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        obj = TestClass()
        obj.method()
        result = profiler.stop()

        found = False
        for key in result.function_stats.keys():
            if key.funcname == "method" and key.classname == "TestClass":
                found = True
                break
        assert found


class TestProfilerEdgeCases:
    def test_profiler_empty_result_on_no_calls(self):
        """Test profiler returns valid result even with no tracked functions"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        result = profiler.stop()

        assert result is not None
        assert isinstance(result.function_stats, dict)

    def test_profiler_stop_without_start(self):
        """Test stop without start returns None"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)
        result = profiler.stop()
        assert result is None

    def test_profiler_start_twice_is_safe(self):
        """Test calling start twice is safe"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        profiler.start()
        result = profiler.stop()
        assert result is not None


class TestProfilerSelfTime:
    def test_profiler_calculates_self_time(self):
        """Test profiler calculates self_time correctly"""
        config = PipelineScopeConfig()
        profiler = Profiler(config)

        profiler.start()
        func_with_calls()
        result = profiler.stop()

        for key, stats in result.function_stats.items():
            if key.funcname == "func_with_calls":
                assert stats.self_time_ms >= 0
                assert stats.self_time_ms <= stats.total_time_ms
