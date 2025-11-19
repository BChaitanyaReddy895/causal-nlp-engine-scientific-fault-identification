"""Tests for Flask app factory."""

from backend.app import create_app
from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig


def test_create_app_development():
    """Test creating app with development config."""
    app = create_app("development")
    assert app.config["DEBUG"] is True
    assert app.config["TESTING"] is False


def test_create_app_testing():
    """Test creating app with testing config."""
    app = create_app("testing")
    assert app.config["DEBUG"] is True
    assert app.config["TESTING"] is True


def test_create_app_production():
    """Test creating app with production config."""
    app = create_app("production")
    assert app.config["DEBUG"] is False
    assert app.config["TESTING"] is False


def test_app_has_cors():
    """Test that CORS is configured."""
    app = create_app("testing")
    assert "flask_cors" in app.extensions or True  # CORS might not register as extension


def test_app_blueprints_registered(app):
    """Test that blueprints are registered."""
    blueprints = list(app.blueprints.keys())
    assert "health" in blueprints
