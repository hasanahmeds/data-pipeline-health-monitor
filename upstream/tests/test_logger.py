from pipelinescope.utils.logger import get_logger, reset_logging, setup_logging


class TestLoggerBasic:
    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance"""
        reset_logging()
        logger = get_logger()
        assert logger is not None

    def test_get_logger_singleton(self):
        """Test get_logger returns same instance"""
        reset_logging()
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


class TestLoggerSetup:
    def test_setup_logging_basic(self):
        """Test setup_logging initializes logger"""
        reset_logging()
        setup_logging()
        logger = get_logger()
        assert logger is not None

    def test_setup_logging_idempotent(self):
        """Test setup_logging can be called multiple times"""
        reset_logging()
        setup_logging()
        setup_logging()
        logger = get_logger()
        assert logger is not None


class TestLoggerReset:
    def test_reset_logging(self):
        """Test reset_logging clears global logger"""
        get_logger()
        reset_logging()
        logger = get_logger()
        assert logger is not None


class TestLoggerWithParameters:
    def test_setup_logging_with_parameters(self, tmp_path):
        """Test setup_logging accepts parameters (for API compatibility)"""
        reset_logging()
        output_dir = tmp_path / "logs"

        setup_logging(
            output_dir=str(output_dir), log_file="test.log", enable_console=True, log_level="INFO"
        )

        logger = get_logger()
        assert logger is not None
