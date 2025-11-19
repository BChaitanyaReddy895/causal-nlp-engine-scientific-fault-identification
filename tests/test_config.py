"""Tests for configuration."""

from backend.config import get_config, DevelopmentConfig, TestingConfig, ProductionConfig


def test_get_config_development():
    """Test getting development config."""
    config = get_config("development")
    assert config == DevelopmentConfig


def test_get_config_testing():
    """Test getting testing config."""
    config = get_config("testing")
    assert config == TestingConfig


def test_get_config_production():
    """Test getting production config."""
    config = get_config("production")
    assert config == ProductionConfig


def test_config_defaults():
    """Test that default config values are set."""
    config = DevelopmentConfig()
    assert config.SECRET_KEY is not None
    assert config.DATABASE_URL is not None
    assert config.KG_PATH is not None
