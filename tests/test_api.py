"""
Tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test API key
TEST_API_KEY = "dev-key-12345"


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "redis_connected" in data


def test_generate_without_api_key():
    """Test that generate endpoint requires API key."""
    response = client.post(
        "/generate",
        json={"prompt": "Test prompt"}
    )
    assert response.status_code == 403  # Forbidden without API key


def test_generate_with_invalid_api_key():
    """Test that invalid API key is rejected."""
    response = client.post(
        "/generate",
        headers={"X-API-Key": "invalid-key"},
        json={"prompt": "Test prompt"}
    )
    assert response.status_code == 401  # Unauthorized


def test_generate_with_valid_api_key():
    """Test successful task submission."""
    response = client.post(
        "/generate",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "prompt": "Test prompt",
            "max_tokens": 50
        }
    )
    assert response.status_code == 202  # Accepted
    data = response.json()
    assert data["status"] == "queued"
    assert "task_id" in data


def test_generate_with_invalid_prompt():
    """Test that empty prompt is rejected."""
    response = client.post(
        "/generate",
        headers={"X-API-Key": TEST_API_KEY},
        json={
            "prompt": "",  # Empty prompt
            "max_tokens": 50
        }
    )
    assert response.status_code == 422  # Validation error


def test_status_endpoint():
    """Test status endpoint."""
    # First submit a task
    response = client.post(
        "/generate",
        headers={"X-API-Key": TEST_API_KEY},
        json={"prompt": "Test prompt"}
    )
    task_id = response.json()["task_id"]
    
    # Check status
    response = client.get(
        f"/status/{task_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["task_id"] == task_id


def test_result_endpoint():
    """Test result endpoint."""
    # First submit a task
    response = client.post(
        "/generate",
        headers={"X-API-Key": TEST_API_KEY},
        json={"prompt": "Test prompt"}
    )
    task_id = response.json()["task_id"]
    
    # Try to get result (may be pending)
    response = client.get(
        f"/result/{task_id}",
        headers={"X-API-Key": TEST_API_KEY}
    )
    assert response.status_code in [200, 202]  # OK or Accepted (if still processing)
