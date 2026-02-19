"""
API tests for health endpoint
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "components" in data
    assert isinstance(data["components"], dict)


def test_health_endpoint_content(client):
    """Test that health endpoint returns expected content"""
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.json()

    # Check expected components
    expected_components = ["preprocessor",
                           "agent", "generator", "safety_reflector"]
    for component in expected_components:
        assert component in data["components"]
        assert data["components"][component] in ["ready", "not initialized"]


def test_health_endpoint_headers(client):
    """Test that health endpoint returns correct headers"""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
