"""Tests for production configuration and environment management."""

from __future__ import annotations

import os
from unittest import mock

from experiment_registry.config import Settings, get_settings
from experiment_registry.logging_config import setup_logging


def test_default_settings() -> None:
    """Verify default fallback configuration values."""
    settings = Settings()
    assert settings.app_name == "Scientific Experiments Registry"
    assert settings.environment in {"development", "test", "production"}
    assert settings.log_level in {"DEBUG", "INFO", "WARNING", "ERROR"}
    assert "sqlite" in settings.database_url
    assert settings.is_development is True or settings.is_production is False


def test_environment_override() -> None:
    """Verify that environment variables properly override defaults."""
    env_vars = {
        "APP_NAME": "Custom Laboratory API",
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///./custom.db",
        "PORT": "9000",
    }
    with mock.patch.dict(os.environ, env_vars):
        custom_settings = Settings()
        assert custom_settings.app_name == "Custom Laboratory API"
        assert custom_settings.environment == "production"
        assert custom_settings.is_production is True
        assert custom_settings.is_development is False
        assert custom_settings.is_test is False
        assert custom_settings.log_level == "DEBUG"
        assert custom_settings.database_url == "sqlite:///./custom.db"
        assert custom_settings.port == 9000


def test_test_environment() -> None:
    """Verify test environment helper."""
    test_settings = Settings(environment="test")
    assert test_settings.is_test is True
    assert test_settings.is_production is False


def test_get_settings_cached() -> None:
    """Verify singleton caching of get_settings()."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_setup_logging() -> None:
    """Verify setup_logging configures logger without errors."""
    logger = setup_logging()
    assert logger.name == "experiment_registry"
