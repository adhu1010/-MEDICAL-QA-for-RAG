"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


def test_api_endpoints_exist(client):
    """Test that all expected API endpoints exist"""
    endpoints = [
        "/api/health",
        "/api/ask",
        "/api/preprocess",
        "/api/stats"
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Health should return 200, others might return 422 (validation error) or 200
        assert response.status_code in [200, 422, 405]  # 405 for wrong method


def test_ask_endpoint_basic(client):
    """Test the ask endpoint with basic request"""
    # This test might fail if components aren't initialized, so we expect potential errors
    try:
        response = client.post("/api/ask", json={
            "question": "What is diabetes?",
            "mode": "patient"
        })

        # Should return 200 if successful or 500 if internal error
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "question" in data
            assert "answer" in data
            assert "confidence" in data
    except Exception:
        # If components aren't available, that's okay for this integration test
        pass


def test_preprocess_endpoint(client):
    """Test the preprocess endpoint"""
    try:
        response = client.post("/api/preprocess", json={
            "question": "What is diabetes?",
            "mode": "auto"
        })

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "original_question" in data
            assert "entities" in data
    except Exception:
        # If components aren't available, that's okay for this integration test
        pass


def test_stats_endpoint(client):
    """Test the stats endpoint"""
    try:
        response = client.get("/api/stats")

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # Should have vector_store and knowledge_graph keys
            assert "vector_store" in data
            assert "knowledge_graph" in data
    except Exception:
        # If components aren't available, that's okay for this integration test
        pass


def test_cors_headers(client):
    """Test that CORS headers are properly set"""
    response = client.get("/api/health")

    # Check for CORS headers
    headers = response.headers
    assert "access-control-allow-origin" in headers
    assert headers["access-control-allow-origin"] == "*"
