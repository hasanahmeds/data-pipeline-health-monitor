import heapq

from pipelinescope.core.config import PipelineScopeConfig
from pipelinescope.core.extrapolation import ExtrapolatedStats, extrapolate
from pipelinescope.core.stats import FunctionKey, FunctionStats, ProfilingResult


class TestExtrapolationBasic:
    def test_extrapolation_scale_factor(self):
        """Test extrapolation calculates correct scale factor"""
        config = PipelineScopeConfig(sample_size=100, expected_size=10000)

        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100, total_time_ms=1000.0)

        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)

        assert key in extrapolated
        assert extrapolated[key].projected_calls == 10000


class TestExtrapolatedStats:
    def test_extrapolated_stats_linear_scaling(self):
        """Test ExtrapolatedStats uses linear scaling"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        original_stats = FunctionStats(
            key=key, call_count=100, total_time_ms=500.0, self_time_ms=300.0
        )

        scale_factor = 100
        extrapolated = ExtrapolatedStats(original_stats, scale_factor)

        assert extrapolated.projected_calls == 10000
        assert extrapolated.projected_time_ms == 50000.0
        assert extrapolated.projected_self_time_ms == 30000.0


class TestExtrapolationPercentages:
    def test_extrapolation_calculates_percentages(self):
        """Test extrapolation calculates percentage of total"""
        config = PipelineScopeConfig(sample_size=10, expected_size=100)

        key1 = FunctionKey(module="test", filename="test.py", funcname="func1", lineno=1)
        key2 = FunctionKey(module="test", filename="test.py", funcname="func2", lineno=2)

        stats1 = FunctionStats(key=key1, total_time_ms=600.0, self_time_ms=600.0)
        stats2 = FunctionStats(key=key2, total_time_ms=400.0, self_time_ms=400.0)

        result = ProfilingResult(
            function_stats={key1: stats1, key2: stats2},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)

        assert extrapolated[key1].percentage_of_total == 60.0
        assert extrapolated[key2].percentage_of_total == 40.0


class TestExtrapolationResourceMetrics:
    def test_extrapolation_preserves_resource_metrics(self):
        """Test extrapolation doesn't scale resource metrics"""
        config = PipelineScopeConfig(sample_size=100, expected_size=10000)

        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(
            key=key,
            call_count=100,
            total_time_ms=1000.0,
            avg_cpu_percent=50.0,
            peak_memory_mb=512.0,
        )

        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)

        assert extrapolated[key].avg_cpu_percent == 50.0
        assert extrapolated[key].peak_memory_mb == 512.0


class TestExtrapolationSmallScaleFactor:
    def test_extrapolation_small_scale_factor(self):
        """Test extrapolation with scale factor < 1"""
        config = PipelineScopeConfig(sample_size=10000, expected_size=100)

        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1000, total_time_ms=5000.0)

        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=5000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)

        assert extrapolated[key].projected_calls == 10
        assert extrapolated[key].projected_time_ms == 50.0


class TestExtrapolationZeroSampleSize:
    def test_extrapolation_zero_sample_size(self):
        """Test extrapolation handles zero sample size"""
        config = PipelineScopeConfig(sample_size=0, expected_size=1000)

        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100)

        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
        assert extrapolated[key].projected_calls == 100


class TestExtrapolationMultipleFunctions:
    def test_extrapolation_multiple_functions(self):
        """Test extrapolation with multiple functions"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        keys = []
        stats_dict = {}

        for i in range(5):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            keys.append(key)
            stats = FunctionStats(
                key=key, call_count=100, total_time_ms=100.0 * (i + 1), self_time_ms=100.0 * (i + 1)
            )
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=1500.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)

        assert len(extrapolated) == 5
        for key in keys:
            assert extrapolated[key].projected_calls == 1000


class TestExtrapolationHotspotMarking:
    def test_extrapolation_marks_top_5_hotspots(self):
        """Test extrapolation marks top 5 functions as hotspots"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        stats_dict = {}
        for i in range(10):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            self_time = 100.0 * (10 - i)
            stats = FunctionStats(
                key=key, call_count=10, total_time_ms=self_time, self_time_ms=self_time
            )
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=5500.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
        top_5 = heapq.nlargest(5, extrapolated.values(), key=lambda s: s.projected_self_time_ms)
        hotspot_count = sum(1 for stats in extrapolated.values() if stats in top_5)
        assert hotspot_count == 5
