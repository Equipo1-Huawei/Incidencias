import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "5.0.0"
    assert "copilot_chat" in data["endpoints"]


def test_triage_schema_validation_error():
    invalid_payload = {"source": "invalid-source", "raw_log": ""}
    response = client.post("/triage", json=invalid_payload)
    assert response.status_code == 422


def test_copilot_chat_endpoint():
    response = client.post("/copilot/chat", json={"message": "What is the impact?"})
    assert response.status_code in [200, 503]
