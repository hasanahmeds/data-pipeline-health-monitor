import json

from pipelinescope.core.extrapolation import ExtrapolatedStats
from pipelinescope.core.stats import CallEdge, FunctionKey, FunctionStats, ProfilingResult
from pipelinescope.data.serializer import serialize_profiling_data


class TestSerializerBasic:
    def test_serializer_creates_json_file(self, tmp_path):
        """Test serializer creates JSON file"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=10, total_time_ms=100.0)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=100.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 1.0)}

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert "metadata" in data
        assert "functions" in data
        assert "call_edges" in data


class TestSerializerMetadata:
    def test_serializer_includes_metadata(self, tmp_path):
        """Test serializer includes metadata"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=5)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=150.5,
            start_timestamp=1000.0,
            end_timestamp=1001.5,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 1.0)}

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        with open(output_path) as f:
            data = json.load(f)

        metadata = data["metadata"]
        assert metadata["total_runtime_ms"] == 150.5
        assert metadata["total_functions"] == 1


class TestSerializerFunctionData:
    def test_serializer_includes_function_data(self, tmp_path):
        """Test serializer includes function statistics"""
        key = FunctionKey(module="mymodule", filename="file.py", funcname="my_func", lineno=42)
        stats = FunctionStats(
            key=key,
            call_count=20,
            total_time_ms=200.0,
            self_time_ms=150.0,
            avg_cpu_percent=30.5,
            peak_memory_mb=256.0,
        )
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=200.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 2.0)}

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        with open(output_path) as f:
            data = json.load(f)

        funcs = data["functions"]
        assert len(funcs) == 1
        func = funcs[0]
        assert func["funcname"] == "my_func"
        assert func["module"] == "mymodule"
        assert func["call_count"] == 20
        assert func["total_time_ms"] == 200.0
        assert func["self_time_ms"] == 150.0


class TestSerializerExtrapolatedMetrics:
    def test_serializer_includes_extrapolated_metrics(self, tmp_path):
        """Test serializer includes extrapolated metrics"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100, total_time_ms=1000.0, self_time_ms=800.0)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 10.0)}

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        with open(output_path) as f:
            data = json.load(f)

        func = data["functions"][0]
        assert func["projected_calls"] == 1000
        assert func["projected_time_ms"] == 10000.0
        assert "percentage_of_total" in func


class TestSerializerCallEdges:
    def test_serializer_includes_call_edges(self, tmp_path):
        """Test serializer includes call edges"""
        caller = FunctionKey(module="test", filename="test.py", funcname="func_a", lineno=1)
        callee = FunctionKey(module="test", filename="test.py", funcname="func_b", lineno=2)

        caller_stats = FunctionStats(key=caller, call_count=1)
        callee_stats = FunctionStats(key=callee, call_count=5)
        edge = CallEdge(caller=caller, callee=callee, call_count=5, total_time_ms=100.0)

        result = ProfilingResult(
            function_stats={caller: caller_stats, callee: callee_stats},
            call_edges={(caller, callee): edge},
            total_runtime_ms=100.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {
            caller: ExtrapolatedStats(caller_stats, 1.0),
            callee: ExtrapolatedStats(callee_stats, 1.0),
        }

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        with open(output_path) as f:
            data = json.load(f)

        edges = data["call_edges"]
        assert len(edges) == 1
        assert edges[0]["call_count"] == 5
        assert edges[0]["total_time_ms"] == 100.0


class TestSerializerMultipleFunctions:
    def test_serializer_handles_multiple_functions(self, tmp_path):
        """Test serializer with multiple functions"""
        stats_dict = {}
        extrapolated_dict = {}

        for i in range(5):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            stats = FunctionStats(key=key, call_count=10, total_time_ms=50.0, self_time_ms=50.0)
            stats_dict[key] = stats
            extrapolated_dict[key] = ExtrapolatedStats(stats, 1.0)

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=250.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated_dict, output_path)

        with open(output_path) as f:
            data = json.load(f)

        assert len(data["functions"]) == 5


class TestSerializerJsonFormatting:
    def test_serializer_uses_compact_json(self, tmp_path):
        """Test serializer uses compact JSON format"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 1.0)}

        output_path = tmp_path / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        content = output_path.read_text()
        assert "\n  " not in content or content.count("\n") < 5


class TestSerializerOutputDirectory:
    def test_serializer_creates_output_directory(self, tmp_path):
        """Test serializer creates output directory if needed"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1.0,
            start_timestamp=0,
            end_timestamp=1,
        )
        extrapolated = {key: ExtrapolatedStats(stats, 1.0)}

        output_path = tmp_path / "nested" / "dir" / "profile_data.json"
        serialize_profiling_data(result, extrapolated, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()
