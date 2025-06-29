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
