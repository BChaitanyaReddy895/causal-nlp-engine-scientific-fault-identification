"""Test configuration and fixtures."""

import pytest
from backend.app import create_app


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI commands."""
    return app.test_cli_runner()
