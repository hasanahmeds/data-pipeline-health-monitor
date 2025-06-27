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

