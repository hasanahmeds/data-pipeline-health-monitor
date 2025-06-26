from pipelinescope.core.config import PipelineScopeConfig
from pipelinescope.core.extrapolation import extrapolate
from pipelinescope.core.stats import FunctionKey, FunctionStats, ProfilingResult
from pipelinescope.reporting.generator import format_time_human, generate_static_report


class TestFormatTimeHuman:
    def test_format_milliseconds(self):
        """Test formatting milliseconds"""
        assert format_time_human(500) == "500ms"
        assert format_time_human(100) == "100ms"

    def test_format_seconds(self):
        """Test formatting seconds"""
        result = format_time_human(5000)
        assert "s" in result

    def test_format_minutes(self):
        """Test formatting minutes"""
        result = format_time_human(60000)
        assert "m" in result

    def test_format_hours(self):
        """Test formatting hours"""
        result = format_time_human(3600000)
        assert "h" in result

    def test_format_days(self):
        """Test formatting days"""
        result = format_time_human(86400000)
        assert "d" in result


class TestGenerateStaticReportBasic:
    def test_generate_report_creates_html_file(self, tmp_path):
        """Test report generation creates HTML file"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=10, total_time_ms=100.0, self_time_ms=100.0)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=100.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig()
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_generate_report_creates_parent_directory(self, tmp_path):
        """Test report generation creates parent directory"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig()
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "nested" / "dir" / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        assert output_path.parent.exists()
        assert output_path.exists()


class TestGenerateReportContent:
    def test_report_includes_title(self, tmp_path):
        """Test report includes dashboard title"""
