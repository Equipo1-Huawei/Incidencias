import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"

def test_webhook_schema_validation_error():
    # Payload inválido sin campos obligatorios
    invalid_payload = {
        "source": "invalid-source",
        "raw_log": ""
    }
    response = client.post("/webhook/n8n", json=invalid_payload)
    assert response.status_code == 422

def test_webhook_valid_security_payload():
    valid_payload = {
        "incident_id": "test-uuid-1234",
        "source": "security-scanner",
        "timestamp": "2026-09-03T10:00:00Z",
        "component": "auth",
        "raw_log": "admin' UNION SELECT 1,2,3--",
        "is_security_event": True,
        "severity_hint": "P1"
    }
    response = client.post("/webhook/n8n", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == "test-uuid-1234"
    assert data["risk_score"] == 10.0
    assert data["severity"] == "P1"
    assert data["escalation_team"] == "SOC"
    assert "checklist" in data
    assert "root_cause_hypothesis" in data
