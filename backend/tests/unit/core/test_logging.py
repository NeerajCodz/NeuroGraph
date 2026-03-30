"""Unit tests for logging module."""

import pytest
from unittest.mock import patch, MagicMock
import structlog


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self, mock_settings):
        """Test that get_logger returns a logger."""
        from src.core.logging import get_logger
        
        logger = get_logger("test.module")
        
        assert logger is not None

    def test_get_logger_with_context(self, mock_settings):
        """Test logger with context."""
        from src.core.logging import get_logger
        
        logger = get_logger("test.module")
        bound_logger = logger.bind(user_id="123", action="test")
        
        assert bound_logger is not None


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_development(self, mock_settings):
        """Test logging setup in development mode."""
        mock_settings.is_development = True
        
        from src.core.logging import setup_logging
        
        # Should not raise
        setup_logging()

    def test_setup_logging_production(self, mock_settings):
        """Test logging setup in production mode."""
        mock_settings.is_development = False
        
        from src.core.logging import setup_logging
        
        # Should not raise
        setup_logging()
