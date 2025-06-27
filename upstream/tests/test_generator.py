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
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig(dashboard_title="My Pipeline")
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        assert "My Pipeline" in content

    def test_report_is_valid_html(self, tmp_path):
        """Test report is valid HTML"""
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

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        assert "<!DOCTYPE" in content or "<html" in content
        assert "</html>" in content


class TestGenerateReportWithMultipleFunctions:
    def test_report_includes_all_functions(self, tmp_path):
        """Test report includes all functions"""
        stats_dict = {}
        for i in range(5):
            key = FunctionKey(module="test", filename="test.py", funcname=f"func{i}", lineno=i + 1)
            stats = FunctionStats(key=key, call_count=10, total_time_ms=50.0, self_time_ms=50.0)
            stats_dict[key] = stats

        result = ProfilingResult(
            function_stats=stats_dict,
            call_edges={},
            total_runtime_ms=250.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig()
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        for i in range(5):
            assert f"func{i}" in content


class TestGenerateReportMetrics:
    def test_report_includes_runtime_metrics(self, tmp_path):
        """Test report includes runtime metrics"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100, total_time_ms=5000.0)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=5000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig()
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        assert "5000" in content or "5s" in content or "time" in content.lower()


class TestGenerateReportScalingFactors:
    def test_report_respects_sample_and_expected_size(self, tmp_path):
        """Test report uses config scaling factors"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=100, total_time_ms=1000.0, self_time_ms=1000.0)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1000.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig(sample_size=100, expected_size=10000)
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        assert ("100" in content and "10000" in content) or "scale" in content.lower()


class TestGenerateReportEmpty:
    def test_report_handles_no_functions(self, tmp_path):
        """Test report generation with no functions"""
        result = ProfilingResult(
            function_stats={},
            call_edges={},
            total_runtime_ms=0.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig()
        extrapolated = {}

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert len(content) > 0


class TestGenerateReportConfigValues:
    def test_report_uses_config_values(self, tmp_path):
        """Test report includes config-based values"""
        key = FunctionKey(module="test", filename="test.py", funcname="func", lineno=1)
        stats = FunctionStats(key=key, call_count=1)
        result = ProfilingResult(
            function_stats={key: stats},
            call_edges={},
            total_runtime_ms=1.0,
            start_timestamp=0,
            end_timestamp=1,
        )

        config = PipelineScopeConfig(
            dashboard_title="Test Pipeline", min_time_threshold_ms=1.5, min_time_percentage=0.2
        )
        extrapolated = extrapolate(result, config)

        output_path = tmp_path / "summary.html"
        generate_static_report(result, extrapolated, config, output_path)

        content = output_path.read_text()
        assert "Test Pipeline" in content
