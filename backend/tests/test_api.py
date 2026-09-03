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
    assert data["version"] == "4.0.0"
    assert "copilot_chat" in data["endpoints"]


def test_webhook_schema_validation_error():
    """Payload invalido sin campos obligatorios debe retornar 422."""
    invalid_payload = {
        "source": "invalid-source",
        "raw_log": ""
    }
    response = client.post("/webhook/n8n", json=invalid_payload)
    assert response.status_code == 422


def test_webhook_valid_security_payload():
    """Payload valido de seguridad debe retornar triage completo."""
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
    assert "guardrail_approved" in data


def test_webhook_infrastructure_payload():
    """Payload de infraestructura debe funcionar."""
    payload = {
        "incident_id": "test-uuid-infra",
        "source": "nextjs",
        "timestamp": "2026-09-03T10:00:00Z",
        "component": "frontend",
        "raw_log": "fatal error: runtime: out of memory allocating 629145600 bytes",
        "is_security_event": False,
        "severity_hint": "P1"
    }
    response = client.post("/webhook/n8n", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["incident_id"] == "test-uuid-infra"
    assert "guardrail_reason" in data


def test_copilot_chat_endpoint():
    """Endpoint del copilot chat debe responder."""
    response = client.post("/copilot/chat", json={"message": "What is the impact?"})
    assert response.status_code in [200, 503]


def test_copilot_chat_with_context():
    """Copilot chat con contexto de incidente."""
    response = client.post("/copilot/chat", json={
        "message": "Should I restart the container?",
        "incident_context": {"component": "frontend", "risk_score": 8.0}
    })
    assert response.status_code in [200, 503]
