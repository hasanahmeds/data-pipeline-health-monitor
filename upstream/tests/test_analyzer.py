from pipelinescope.core.config import PipelineScopeConfig
from pipelinescope.core.extrapolation import ExtrapolatedStats, extrapolate
from pipelinescope.core.stats import FunctionKey, FunctionStats, ProfilingResult
from pipelinescope.reporting.analyzer import (
    HotspotFunction,
    ModuleAggregate,
    _should_include_function,
    aggregate_by_module,
    extract_hotspots,
    get_all_functions,
)


class TestHotspotFunctionBasic:
    def test_hotspot_function_creation(self):
        """Test HotspotFunction creation"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100, total_time_ms=500.0, self_time_ms=400.0)
        extrapolated = ExtrapolatedStats(stats, 10.0)

        hotspot = HotspotFunction(key, stats, extrapolated)
        assert hotspot.call_count == 100
        assert hotspot.display_name is not None


class TestHotspotExtraction:
    def test_extract_hotspots_top_5(self):
        """Test extract_hotspots returns top 5 by default"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        stats_dict = {}
        for i in range(10):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            stats = FunctionStats(
                key=key,
                call_count=10,
                total_time_ms=100.0 * (10 - i),
                self_time_ms=100.0 * (10 - i),
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
        hotspots = extract_hotspots(result, extrapolated, top_n=5)

        assert len(hotspots) <= 5
        assert all(isinstance(h, HotspotFunction) for h in hotspots)

    def test_extract_hotspots_sorted_by_time(self):
        """Test hotspots are sorted by projected self time"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        keys = []
        stats_dict = {}
        for i in range(3):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            keys.append(key)
            stats = FunctionStats(
                key=key, call_count=10, total_time_ms=100.0 * (i + 1), self_time_ms=100.0 * (i + 1)
            )
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=600.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
        hotspots = extract_hotspots(result, extrapolated, top_n=5)

        for i in range(len(hotspots) - 1):
            assert hotspots[i].projected_self_time_ms >= hotspots[i + 1].projected_self_time_ms


class TestModuleAggregation:
    def test_aggregate_by_module_basic(self):
        """Test module aggregation"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        key1 = FunctionKey(module="module1", filename="module1.py", funcname="func1", lineno=1)
        key2 = FunctionKey(module="module2", filename="module2.py", funcname="func2", lineno=1)

        stats1 = FunctionStats(key=key1, call_count=10, total_time_ms=100.0, self_time_ms=100.0)
        stats2 = FunctionStats(key=key2, call_count=20, total_time_ms=200.0, self_time_ms=200.0)

        result = ProfilingResult(
            function_stats={key1: stats1, key2: stats2},
            call_edges={},
            total_runtime_ms=300.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
        aggregates = aggregate_by_module(result, extrapolated)

        assert len(aggregates) >= 2
        assert all(isinstance(a, ModuleAggregate) for a in aggregates)

    def test_aggregate_by_module_function_count(self):
        """Test module aggregate counts functions correctly"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        stats_dict = {}
        for i in range(3):
            key = FunctionKey(
                module="mymodule", filename="mymodule.py", funcname=f"func{i}", lineno=i + 1
            )
            stats = FunctionStats(key=key, call_count=10, total_time_ms=50.0, self_time_ms=50.0)
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=150.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
        aggregates = aggregate_by_module(result, extrapolated)

        my_module = next((a for a in aggregates if a.module_name == "mymodule"), None)
        assert my_module is not None
        assert my_module.function_count == 3

    def test_aggregate_by_module_sorting(self):
        """Test module aggregates are sorted by projected time"""
        config = PipelineScopeConfig(sample_size=100, expected_size=1000)

        stats_dict = {}
        for i in range(3):
            key = FunctionKey(
                module=f"module{i}", filename=f"module{i}.py", funcname="func", lineno=1
            )

            stats = FunctionStats(
                key=key, call_count=1, total_time_ms=1000.0 * (i + 1), self_time_ms=1000.0 * (i + 1)
            )
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=6000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        extrapolated = extrapolate(result, config)
