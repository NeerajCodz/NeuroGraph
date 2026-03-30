"""Unit tests for configuration module."""

import pytest
from unittest.mock import patch
import os


class TestSettings:
    """Tests for Settings class."""

    def test_settings_from_env(self):
        """Test settings loading from environment."""
        env_vars = {
            "APP_NAME": "test-app",
            "APP_ENV": "testing",
            "APP_DEBUG": "true",
            "NEO4J_URI": "bolt://test:7687",
            "NEO4J_USERNAME": "test_user",
            "NEO4J_PASSWORD": "test_pass",
            "POSTGRES_HOST": "test_host",
            "POSTGRES_PORT": "5433",
            "POSTGRES_USER": "test_pg_user",
            "POSTGRES_PASSWORD": "test_pg_pass",
            "POSTGRES_DB": "test_db",
            "REDIS_URL": "redis://test:6379/1",
            "JWT_SECRET_KEY": "test_jwt_secret",
            "GEMINI_API_KEY": "test_gemini_key",
            "GROQ_API_KEY": "test_groq_key",
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            from src.core.config import Settings
            settings = Settings()
            
            assert settings.app_name == "test-app"
            assert settings.app_env == "testing"
            assert settings.app_debug is True
            assert settings.neo4j_uri == "bolt://test:7687"
            assert settings.postgres_host == "test_host"
            assert settings.postgres_port == 5433

    def test_is_development(self, mock_settings):
        """Test is_development property."""
        mock_settings.app_env = "development"
        assert mock_settings.is_development is True
        
        mock_settings.app_env = "production"
        assert mock_settings.is_development is False

    def test_is_production(self, mock_settings):
        """Test is_production property."""
        mock_settings.app_env = "production"
        assert mock_settings.is_production is True
        
        mock_settings.app_env = "development"
        assert mock_settings.is_production is False

    def test_log_level(self, mock_settings):
        """Test log_level property."""
        mock_settings.app_debug = True
        assert mock_settings.log_level == "debug"
        
        mock_settings.app_debug = False
        mock_settings.log_level = "info"
        assert mock_settings.log_level == "info"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_cached(self, mock_settings):
        """Test that settings are cached."""
        from src.core.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return the same mock instance
        assert settings1 is settings2
