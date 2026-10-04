"""
Unit tests for the Flask public-facing interface.

Verifies that the Flask web application is directly instantiated at module level
without an application factory, and that the index route serves a completely
blank document devoid of UI/UX components.
"""

from unittest.mock import patch
from flask import Flask
import pytest
import requests

from backend.flask_app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_flask_app_module_level_instantiation():
    """Verify the Flask app is directly instantiated without an application factory."""
    assert isinstance(app, Flask)
    assert not hasattr(app, "create_app")


def test_index_route_blank_content(client):
    """Verify GET / returns 200 and a blank HTML document devoid of UI/UX elements."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.content_type

    html_content = response.data.decode("utf-8")
    lower_content = html_content.lower()

    # Verify standard HTML document structure is present
    assert "<!doctype html>" in lower_content
    assert "<html" in lower_content
    assert "<head" in lower_content
    assert "<body" in lower_content

    # Verify absence of UI/UX components
    assert "<style" not in lower_content
    assert "<link rel=\"stylesheet\"" not in lower_content
    assert "<script" not in lower_content
    assert "<button" not in lower_content
    assert "<nav" not in lower_content
    assert "<form" not in lower_content
    assert "<input" not in lower_content
    assert "<div" not in lower_content


def test_health_route(client):
    """Verify GET /health returns 200 and expected status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"status": "ok", "service": "flask"}


@patch("backend.flask_app.requests.get")
def test_fastapi_health_reachable(mock_get, client):
    """Verify GET /fastapi-health returns 200 when backend is reachable."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "healthy"}

    response = client.get("/fastapi-health")
    assert response.status_code == 200
    data = response.get_json()
    assert data == {"fastapi": {"status": "healthy"}}


@patch("backend.flask_app.requests.get")
def test_fastapi_health_unreachable(mock_get, client):
    """Verify GET /fastapi-health returns 503 when backend is unreachable."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

    response = client.get("/fastapi-health")
    assert response.status_code == 503
    data = response.get_json()
    assert "error" in data


def test_blueprint_registration():
    """Verify the training bridge blueprint is registered on the Flask application."""
    assert "bridge" in app.blueprints
