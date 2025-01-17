"""Common test fixtures."""

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test_secret_key"
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create an application context."""
    with app.app_context():
        yield


@pytest.fixture
def request_context(app, app_context):
    """Create a request context."""
    with app.test_request_context():
        yield
