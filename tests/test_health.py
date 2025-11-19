"""Tests for health endpoints."""

import pytest


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "causal-nlp-engine"
    assert "timestamp" in data


def test_index(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "Causal-NLP Engine for Fake Scientific Claims Detection"
    assert data["status"] == "running"
