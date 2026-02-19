"""
Unit tests for configuration
"""
import os
import tempfile
from backend.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values"""
    settings = Settings()

    # Check default values
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert settings.debug_mode is True
    assert settings.log_level == "INFO"
    assert settings.log_file == "./logs/app.log"
    assert settings.vector_store_path == "./vector_store"
    assert settings.top_k_vector == 5
    assert settings.top_k_kg == 3
    assert settings.similarity_threshold == 0.7
    assert settings.enable_safety_reflection is True
    assert settings.enable_content_filter is True


def test_settings_from_env():
    """Test that settings can be overridden from environment variables"""
    # Create temporary environment
    original_env = os.environ.copy()

    try:
        # Set test environment variables
        os.environ["APP_HOST"] = "127.0.0.1"
        os.environ["APP_PORT"] = "9000"
        os.environ["DEBUG_MODE"] = "False"
        os.environ["LOG_LEVEL"] = "DEBUG"

        # Create settings with new environment
        settings = Settings()

        assert settings.app_host == "127.0.0.1"
        assert settings.app_port == 9000
        assert settings.debug_mode is False
        assert settings.log_level == "DEBUG"

    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


def test_settings_types():
    """Test that settings have correct types"""
    settings = Settings()

    assert isinstance(settings.app_host, str)
    assert isinstance(settings.app_port, int)
    assert isinstance(settings.debug_mode, bool)
    assert isinstance(settings.log_level, str)
    assert isinstance(settings.log_file, str)
    assert isinstance(settings.vector_store_path, str)
    assert isinstance(settings.top_k_vector, int)
    assert isinstance(settings.top_k_kg, int)
    assert isinstance(settings.similarity_threshold, float)
    assert isinstance(settings.enable_safety_reflection, bool)
    assert isinstance(settings.enable_content_filter, bool)
